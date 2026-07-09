"""aios_api.connectors —— 数据源连接器（4 类关系型 DB）。"""
from .base import DatasourceConnector, TableInfo
from .factory import build_connector, supported_types

__all__ = ["DatasourceConnector", "TableInfo", "build_connector", "supported_types"]