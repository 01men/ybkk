"""tests.datasource_service —— 数据源接入业务逻辑测试（mock 连接器）。"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from aios_api.connectors.base import ConnectionResult, FieldInfo, TableInfo
from aios_api.errors import AiosError, ErrorCode
from aios_api.models import DatasourceStatus
from aios_api.services import datasource_service


def _ok_conn_result(n_tables: int = 3) -> ConnectionResult:
    tables = [
        TableInfo(
            schema_name="public",
            table_name=f"t{i}",
            fields=[FieldInfo(name="id", data_type="int", nullable=False, is_primary_key=True)],
        )
        for i in range(n_tables)
    ]
    return ConnectionResult(connected=True, tables=tables)


class _FakeRepo:
    """最小 fake，覆盖 service 用到的 3 个方法。"""

    def __init__(self) -> None:
        self.created: list[tuple[str, str]] = []
        self.statuses: list[tuple[str, DatasourceStatus]] = []

    async def create(self, type_: str, encrypted: str):
        from aios_api.models import Datasource
        from datetime import datetime, UTC

        ds = Datasource(
            id=f"ds-{len(self.created)}",
            type=type_,
            connection_json_encrypted=encrypted,
            status=DatasourceStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.created.append((type_, encrypted))
        return ds

    async def update_status(self, ds_id: str, status: DatasourceStatus) -> None:
        self.statuses.append((ds_id, status))

    async def get(self, ds_id: str):
        return None


class TestDatasourceServiceCreate:
    @pytest.fixture
    def service(self, monkeypatch: pytest.MonkeyPatch) -> datasource_service.DatasourceService:
        # 固定 KMS 密钥
        monkeypatch.setenv("AIOS_KMS_KEY", "0" * 64)
        import aios_api.secret as sm

        sm._fernet = None
        return datasource_service.DatasourceService(_FakeRepo())  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_happy_path(self, service, monkeypatch) -> None:
        monkeypatch.setattr(
            "aios_api.connectors.factory.build_connector",
            lambda t, c: AsyncMock(
                test_connection=AsyncMock(return_value=_ok_conn_result(n_tables=2)),
                close=AsyncMock(),
            ),
        )
        req = datasource_service.DatasourceCreateRequest(
            type="mysql",
            connection={
                "host": "db.local",
                "port": 3306,
                "user": "r",
                "password": "p",
                "db": "d",
                "read_only_account_ack": True,
            },
        )
        result = await service.create(req)
        assert result.status == DatasourceStatus.CONNECTED.value
        assert result.tables_discovered == 2
        assert result.fields_inferred == 2  # 每张表 1 字段

    @pytest.mark.asyncio
    async def test_missing_readonly_ack_raises(self, service) -> None:
        req = datasource_service.DatasourceCreateRequest(
            type="mysql",
            connection={"host": "h", "port": 3306, "user": "u", "password": "p", "db": "d"},
        )
        with pytest.raises(AiosError) as exc_info:
            await service.create(req)
        assert exc_info.value.code == ErrorCode.E_DS_NO_PERMISSION

    @pytest.mark.asyncio
    async def test_missing_required_field_raises(self, service) -> None:
        req = datasource_service.DatasourceCreateRequest(
            type="mysql",
            connection={"host": "h", "port": 3306, "user": "u", "db": "d", "read_only_account_ack": True},
        )
        with pytest.raises(AiosError) as exc_info:
            await service.create(req)
        assert exc_info.value.code == ErrorCode.E_VAL_REQUIRED

    @pytest.mark.asyncio
    async def test_connection_failure_marks_failed(self, service, monkeypatch) -> None:
        monkeypatch.setattr(
            "aios_api.connectors.factory.build_connector",
            lambda t, c: AsyncMock(
                test_connection=AsyncMock(
                    return_value=ConnectionResult(False, error_code="E_DS_AUTH", error_message="bad pwd")
                ),
                close=AsyncMock(),
            ),
        )
        req = datasource_service.DatasourceCreateRequest(
            type="postgres",
            connection={
                "host": "db.local",
                "port": 5432,
                "user": "r",
                "password": "wrong",
                "db": "d",
                "read_only_account_ack": True,
            },
        )
        result = await service.create(req)
        assert result.status == DatasourceStatus.FAILED.value
        assert "bad pwd" in (result.error or "")

    @pytest.mark.asyncio
    async def test_credential_is_encrypted_in_storage(self, service, monkeypatch) -> None:
        repo = service._repo  # type: ignore[attr-defined]
        monkeypatch.setattr(
            "aios_api.connectors.factory.build_connector",
            lambda t, c: AsyncMock(
                test_connection=AsyncMock(return_value=_ok_conn_result(n_tables=1)),
                close=AsyncMock(),
            ),
        )
        req = datasource_service.DatasourceCreateRequest(
            type="mysql",
            connection={
                "host": "h",
                "port": 3306,
                "user": "u",
                "password": "supersecret",
                "db": "d",
                "read_only_account_ack": True,
            },
        )
        await service.create(req)
        # 落库的密文不应含明文密码
        assert len(repo.created) == 1
        _, encrypted = repo.created[0]
        assert "supersecret" not in encrypted