"""SQL Server 连接器（aioodbc 驱动）。

注意：SQL Server 的元数据查询走 sys.tables / sys.columns。
"""
from __future__ import annotations

from typing import Any

from ..errors import datasource_auth, datasource_no_permission, datasource_timeout
from .base import ConnectionResult, DatasourceConnector, FieldInfo, TableInfo


class SqlServerConnector(DatasourceConnector):
    type_name = "sqlserver"

    def __init__(self, connection: dict[str, Any]) -> None:
        super().__init__(connection)
        self._conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={connection['host']},{connection.get('port', 1433)};"
            f"DATABASE={connection['db']};UID={connection['user']};PWD={connection['password']}"
        )
        self._pool = None

    async def test_connection(self) -> ConnectionResult:
        try:
            import aioodbc
        except ImportError:
            return ConnectionResult(
                connected=False, error_code="E_SYS_MISSING_DEP", error_message="缺少依赖: aioodbc"
            )

        try:
            self._pool = await aioodbc.create_pool(dsn=self._conn_str, timeout=10)
        except Exception as e:
            err_msg = str(e).lower()
            if "login" in err_msg or "auth" in err_msg:
                err = datasource_auth("sqlserver")
                return ConnectionResult(False, error_code=err.code.value, error_message=err.message)
            if "timeout" in err_msg:
                err = datasource_timeout("sqlserver", timeout_s=10)
                return ConnectionResult(False, error_code=err.code.value, error_message=err.message)
            return ConnectionResult(False, error_code="E_DS_UNKNOWN", error_message=str(e))

        try:
            async with self._pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    row = await cur.fetchone()
                    if not row or row[0] != 1:
                        return ConnectionResult(False, error_code="E_DS_INVALID", error_message="SELECT 1 failed")

                    # 验证只读：尝试建表
                    try:
                        await cur.execute(
                            "CREATE TABLE _aios_write_probe (id INT)"
                        )
                        await cur.execute("DROP TABLE _aios_write_probe")
                        err = datasource_no_permission("sqlserver")
                        return ConnectionResult(False, error_code=err.code.value, error_message=err.message)
                    except Exception:
                        pass

            tables = await self.extract_schema()
            return ConnectionResult(connected=True, tables=tables)
        except Exception as e:
            return ConnectionResult(False, error_code="E_DS_QUERY_FAILED", error_message=str(e))

    async def extract_schema(self) -> list[TableInfo]:
        if self._pool is None:
            return []
        sql = """
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        cols_sql = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """

        tables: list[TableInfo] = []
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                rows = await cur.fetchall()
                for schema, name in rows:
                    await cur.execute(cols_sql, (schema, name))
                    cols = await cur.fetchall()
                    fields = [
                        FieldInfo(
                            name=c[0],
                            data_type=c[1],
                            nullable=(c[2] == "YES"),
                            is_primary_key=False,
                        )
                        for c in cols
                    ]
                    tables.append(
                        TableInfo(schema_name=schema, table_name=name, fields=fields)
                    )
        return tables

    async def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None