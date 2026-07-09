"""tests.connectors —— 连接器单元测试（Mock 驱动，不需要真实数据库）。"""
from __future__ import annotations

import pytest

from aios_api.connectors import build_connector, supported_types


class TestConnectorFactory:
    def test_supported_types(self) -> None:
        types = supported_types()
        assert "mysql" in types
        assert "postgres" in types
        assert "sqlserver" in types
        assert "oracle" in types

    def test_build_mysql_connector(self) -> None:
        c = build_connector("mysql", {"host": "localhost", "port": 3306, "user": "u", "password": "p", "db": "d"})
        assert c.type_name == "mysql"

    def test_build_unsupported_raises_error(self) -> None:
        from aios_api.errors import AiosError, ErrorCode

        with pytest.raises(AiosError) as exc_info:
            build_connector("sqlite", {})
        assert exc_info.value.code == ErrorCode.E_VAL_INVALID