"""Oracle 连接器（python-oracledb 异步模式）。"""
from __future__ import annotations

from typing import Any

from ..errors import datasource_auth, datasource_no_permission, datasource_timeout
from .base import ConnectionResult, DatasourceConnector, FieldInfo, TableInfo


class OracleConnector(DatasourceConnector):
    type_name = "oracle"

    def __init__(self, connection: dict[str, Any]) -> None:
        super().__init__(connection)
        self._dsn = (
            f"{connection['host']}:{connection.get('port', 1521)}/{connection.get('service_name', 'ORCLPDB1')}"
        )
        self._user = connection["user"]
        self._password = connection["password"]
        self._pool = None

    async def test_connection(self) -> ConnectionResult:
        try:
            import oracledb
        except ImportError:
            return ConnectionResult(
                connected=False, error_code="E_SYS_MISSING_DEP", error_message="缺少依赖: oracledb"
            )

        try:
            # python-oracledb 2.0+ 默认 thin mode
            self._pool = await oracledb.create_pool_async(
                dsn=self._dsn,
                user=self._user,
                password=self._password,
                min=1,
                max=2,
                timeout=10,
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "invalid username" in err_msg or "ora-01017" in err_msg:
                err = datasource_auth("oracle")
                return ConnectionResult(False, error_code=err.code.value, error_message=err.message)
            if "timeout" in err_msg or "ora-12535" in err_msg:
                err = datasource_timeout("oracle", timeout_s=10)
                return ConnectionResult(False, error_code=err.code.value, error_message=err.message)
            return ConnectionResult(False, error_code="E_DS_UNKNOWN", error_message=str(e))

        try:
            async with self._pool.acquire() as conn:
                v = await conn.fetchval("SELECT 1 FROM DUAL")
                if v != 1:
                    return ConnectionResult(False, error_code="E_DS_INVALID", error_message="SELECT 1 failed")

                # 验证只读：尝试建表（ORACLE 通常需要 CREATE ANY TABLE 权限）
                try:
                    await conn.execute(
                        "CREATE TABLE _aios_write_probe (id NUMBER)"
                    )
                    await conn.execute("DROP TABLE _aios_write_probe")
                    err = datasource_no_permission("oracle")
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
        # Oracle 没有 information_schema；走 user_tables + user_tab_columns
        sql = """
        SELECT table_name, num_rows
        FROM user_tables
        ORDER BY table_name
        """
        cols_sql = """
        SELECT column_name, data_type, nullable
        FROM user_tab_columns
        WHERE table_name = :tname
        ORDER BY column_id
        """

        tables: list[TableInfo] = []
        async with self._pool.acquire() as conn:
            rows = await conn.fetchall(sql)
            for r in rows:
                name, est_rows = r[0], r[1]
                cols = await conn.fetchall(cols_sql, tname=name.upper())
                fields = [
                    FieldInfo(
                        name=c[0],
                        data_type=c[1],
                        nullable=(c[2] == "Y"),
                        is_primary_key=False,
                    )
                    for c in cols
                ]
                tables.append(
                    TableInfo(
                        schema_name=self._user.upper(),
                        table_name=name,
                        fields=fields,
                        estimated_rows=est_rows,
                    )
                )
        return tables

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None