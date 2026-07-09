"""数据源管理 API（参见 TASK-020 + 02-design-doc.md §2.4）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator

from ...db import get_session
from ...repositories import DatasourceRepository
from ...services import datasource_service as ds_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/datasources", tags=["datasources"])


# -----------------------------------------------------------------------------
# Pydantic schema
# -----------------------------------------------------------------------------


class ConnectionPayload(BaseModel):
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    user: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=512)
    db: str = Field(..., min_length=1, max_length=128)
    ssl: bool = False
    read_only_account_ack: bool = Field(..., description="必须为 True")

    @field_validator("read_only_account_ack")
    @classmethod
    def must_ack_readonly(cls, v: bool) -> bool:
        if not v:
            raise ValueError("read_only_account_ack must be True")
        return v


class CreateDatasourceBody(BaseModel):
    type: str = Field(..., pattern="^(mysql|postgres|sqlserver|oracle)$")
    connection: ConnectionPayload


class DatasourceResponse(BaseModel):
    id: str
    status: str
    tables_discovered: int
    fields_inferred: int
    error: str | None = None


# -----------------------------------------------------------------------------
# 依赖注入
# -----------------------------------------------------------------------------


async def get_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> DatasourceRepository:
    return DatasourceRepository(session)


# -----------------------------------------------------------------------------
# 端点
# -----------------------------------------------------------------------------


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DatasourceResponse,
    summary="添加数据源",
)
async def create_datasource(
    body: CreateDatasourceBody,
    repo: Annotated[DatasourceRepository, Depends(get_repo)],
) -> DatasourceResponse:
    """添加一个只读数据源。系统会：
    1. 加密凭证落库
    2. 测试连接
    3. 验证只读权限
    4. 抽取表/字段元数据

    失败时返回 201 + status=FAILED + error 字段（不抛 4xx，便于 UI 一次性展示）。
    """
    svc = ds_service.DatasourceService(repo)
    req = ds_service.DatasourceCreateRequest(
        type=body.type,
        connection=body.connection.model_dump(),
    )
    result = await svc.create(req)
    return DatasourceResponse(
        id=result.id,
        status=result.status,
        tables_discovered=result.tables_discovered,
        fields_inferred=result.fields_inferred,
        error=result.error,
    )


@router.get("/{datasource_id}", response_model=DatasourceResponse)
async def get_datasource(
    datasource_id: str,
    repo: Annotated[DatasourceRepository, Depends(get_repo)],
) -> DatasourceResponse:
    svc = ds_service.DatasourceService(repo)
    result = await svc.get(datasource_id)
    if result is None:
        from ...errors import AiosError, ErrorCode

        raise AiosError(
            ErrorCode.E_DS_NOT_FOUND,
            f"数据源不存在: {datasource_id}",
            context={"datasource_id": datasource_id},
        )
    return DatasourceResponse(
        id=result.id,
        status=result.status,
        tables_discovered=result.tables_discovered,
        fields_inferred=result.fields_inferred,
        error=result.error,
    )


@router.get("", response_model=list[DatasourceResponse])
async def list_datasources(
    repo: Annotated[DatasourceRepository, Depends(get_repo)],
) -> list[DatasourceResponse]:
    items = await repo.list_all()
    return [
        DatasourceResponse(
            id=ds.id,
            status=ds.status.value,
            tables_discovered=0,
            fields_inferred=0,
        )
        for ds in items
    ]