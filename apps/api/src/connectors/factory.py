"""连接器工厂。"""
from __future__ import annotations

from typing import Any

from ..errors import AiosError, ErrorCode
from .base import DatasourceConnector
from .mysql import MySQLConnector
from .postgres import PostgresConnector
from .oracle import OracleConnector
from .sqlserver import SqlServerConnector

_REGISTRY: dict[str, type[DatasourceConnector]] = {
    "mysql": MySQLConnector,
    "postgres": PostgresConnector,
    "sqlserver": SqlServerConnector,
    "oracle": OracleConnector,
}


def supported_types() -> list[str]:
    return sorted(_REGISTRY.keys())


def build_connector(ds_type: str, connection: dict[str, Any]) -> DatasourceConnector:
    """根据 type 创建连接器。"""
    cls = _REGISTRY.get(ds_type)
    if cls is None:
        raise AiosError(
            ErrorCode.E_VAL_INVALID,
            f"不支持的数据源类型: {ds_type}",
            context={"supported_types": supported_types(), "given": ds_type},
        )
    return cls(connection)