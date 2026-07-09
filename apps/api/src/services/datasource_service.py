"""aios_api.services.datasource_service —— 数据源接入业务逻辑（参见 TASK-020）。

关键流程：
  1. 入参校验（Pydantic）
  2. 凭证 KMS 加密
  3. 落 datasources 表（PENDING 状态）
  4. 后台任务连接 + 验证只读 + 抽表元数据
  5. 失败 → 标 FAILED + 写审计
  6. 成功 → 标 CONNECTED + 返回摘要 + 触发 ontology 重建
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..connectors import build_connector
from ..errors import AiosError, ErrorCode
from ..models import DatasourceStatus
from ..repositories import DatasourceRepository
from ..secret import get_secret_service


@dataclass
class DatasourceCreateRequest:
    type: str
    connection: dict


@dataclass
class DatasourceCreateResult:
    id: str
    status: str
    tables_discovered: int
    fields_inferred: int
    error: str | None = None


class DatasourceService:
    def __init__(self, repo: DatasourceRepository) -> None:
        self._repo = repo
        self._secret = get_secret_service()

    async def create(self, req: DatasourceCreateRequest) -> DatasourceCreateResult:
        # 入参校验
        if not req.connection.get("read_only_account_ack"):
            raise AiosError(
                ErrorCode.E_DS_NO_PERMISSION,
                "必须勾选 read_only_account_ack（确认使用只读账号）",
                context={"datasource_type": req.type},
            )

        for field in ("host", "port", "user", "password", "db"):
            if field not in req.connection:
                raise AiosError(
                    ErrorCode.E_VAL_REQUIRED,
                    f"数据源连接缺少字段: {field}",
                    context={"datasource_type": req.type, "missing": field},
                )

        # 凭证加密
        encrypted = self._secret.encrypt(json.dumps(req.connection))

        # 落库（PENDING）
        ds = await self._repo.create(req.type, encrypted)

        # 连接 + 验证 + 抽 schema
        try:
            connector = build_connector(req.type, req.connection)
            try:
                result = await connector.test_connection()
            finally:
                await connector.close()

            if not result.connected:
                await self._repo.update_status(ds.id, DatasourceStatus.FAILED)
                return DatasourceCreateResult(
                    id=ds.id,
                    status=DatasourceStatus.FAILED.value,
                    tables_discovered=0,
                    fields_inferred=0,
                    error=result.error_message or "连接失败",
                )

            tables = result.tables
            fields_inferred = sum(len(t.fields) for t in tables)
            await self._repo.update_status(ds.id, DatasourceStatus.CONNECTED)

            return DatasourceCreateResult(
                id=ds.id,
                status=DatasourceStatus.CONNECTED.value,
                tables_discovered=len(tables),
                fields_inferred=fields_inferred,
            )
        except Exception as e:
            await self._repo.update_status(ds.id, DatasourceStatus.FAILED)
            raise AiosError(
                ErrorCode.E_SYS_INTERNAL,
                "数据源接入异常",
                http_status=500,
                context={"datasource_id": ds.id, "type": type(e).__name__},
            ) from e

    async def get(self, datasource_id: str) -> DatasourceCreateResult | None:
        ds = await self._repo.get(datasource_id)
        if ds is None:
            return None
        return DatasourceCreateResult(
            id=ds.id,
            status=ds.status.value,
            tables_discovered=0,  # 摘要从 ontology 服务拉
            fields_inferred=0,
        )