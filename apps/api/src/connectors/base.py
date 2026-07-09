"""数据源连接器抽象接口。

设计原则：
  - 所有连接器**只读**；不允许任何写操作
  - 测试连接时主动跑一条 SELECT 1 验证只读账号权限
  - 表元数据走 information_schema
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldInfo:
    name: str
    data_type: str
    nullable: bool
    is_primary_key: bool = False
    comment: str | None = None


@dataclass
class TableInfo:
    schema_name: str
    table_name: str
    fields: list[FieldInfo] = field(default_factory=list)
    estimated_rows: int | None = None
    comment: str | None = None


@dataclass
class ConnectionResult:
    connected: bool
    tables: list[TableInfo] = field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None


class DatasourceConnector(ABC):
    """关系型 DB 连接器抽象基类。"""

    type_name: str

    def __init__(self, connection: dict[str, Any]) -> None:
        self._conn = connection

    @abstractmethod
    async def test_connection(self) -> ConnectionResult:
        """测试连接 + 验证只读权限。

        必须：
          1. 建立连接
          2. 跑 SELECT 1
          3. 尝试一条写操作（INSERT/UPDATE），预期失败（账号只读）
          4. 拉表元数据
        """

    @abstractmethod
    async def close(self) -> None:
        """关闭连接。"""

    @abstractmethod
    async def extract_schema(self) -> list[TableInfo]:
        """从 information_schema 抽表 + 字段元数据。"""