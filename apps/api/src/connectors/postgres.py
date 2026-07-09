"""PostgreSQL 连接器（asyncpg 驱动）。"""
from __future__ import annotations

from typing import Any

from ..errors import datasource_auth, datasource_no_permission, datasource_timeout
from .base import ConnectionResult, DatasourceConnector, FieldInfo, TableInfo


class PostgresConnector(DatasourceConnector):
    type_name = "postgres"

    def __init__(self, connection: dict[str, Any]) -> None:
        super().__init__(connection)
        self._dsn = (
            f"postgresql://{connection['user']}:{connection['password']}"
            f"@{connection['host']}:{connection.get('port', 5432)}/{connection['db']}"
        )
        self._conn = None

    async def test_connection(self) -> ConnectionResult:
        try:
            import asyncpg
        except ImportError:
            return ConnectionResult(
                connected=False,
                error_code="E_SYS_MISSING_DEP",
                error_message="缺少依赖: asyncpg",
            )

        try:
            self._conn = await asyncpg.connect(self._dsn, timeout=10)
        except Exception as e:
            err_msg = str(e).lower()
            if "password authentication" in err_msg or "authentication" in err_msg:
                err = datasource_auth("postgres")
                return ConnectionResult(False, error_code=err.code.value, error_message=err.message)
            if "timeout" in err_msg:
                err = datasource_timeout("postgres", timeout_s=10)
                return ConnectionResult(False, error_code=err.code.value, error_message=err.message)
            return ConnectionResult(False, error_code="E_DS_UNKNOWN", error_message=str(e))

        try:
            v = await self._conn.fetchval("SELECT 1")
            if v != 1:
                return ConnectionResult(False, error_code="E_DS_INVALID", error_message="SELECT 1 failed")

            # 只读权限验证：尝试建临时表，预期失败
            try:
                await self._conn.execute("CREATE TEMP TABLE _aios_write_probe (id INT)")
                await self._conn.execute("DROP TABLE _aios_write_probe")
                err = datasource_no_permission("postgres")
                return ConnectionResult(False, error_code=err.code.value, error_message=err.message)
            except Exception:
                pass

            tables = await self.extract_schema()
            return ConnectionResult(connected=True, tables=tables)
        except Exception as e:
            return ConnectionResult(connected=False, error_code="E_DS_QUERY_FAILED", error_message=str(e))

    async def extract_schema(self) -> list[TableInfo]:
        if self._conn is None:
            return []
        sql = """
        SELECT table_schema, table_name, obj_description(c.oid) AS comment
        FROM information_schema.tables t
        JOIN pg_class c ON c.relname = t.table_name
        JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.table_schema
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
          AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name
        """
        cols_sql = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = $1 AND table_name = $2
        ORDER BY ordinal_position
        """

        rows = await self._conn.fetch(sql)
        tables: list[TableInfo] = []
        for r in rows:
            cols = await self._conn.fetch(cols_sql, r["table_schema"], r["table_name"])
            fields = [
                FieldInfo(
                    name=c["column_name"],
                    data_type=c["data_type"],
                    nullable=(c["is_nullable"] == "YES"),
                    is_primary_key=False,
                    comment=None,
                )
                for c in cols
            ]
            tables.append(
                TableInfo(
                    schema_name=r["table_schema"],
                    table_name=r["table_name"],
                    fields=fields,
                    estimated_rows=None,
                    comment=r["comment"],
                )
            )
        return tables

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None