"""MySQL 连接器（aiomysql 驱动）。"""
from __future__ import annotations

from typing import Any

from ..errors import ErrorCode, datasource_auth, datasource_no_permission, datasource_timeout
from .base import ConnectionResult, DatasourceConnector, FieldInfo, TableInfo


class MySQLConnector(DatasourceConnector):
    type_name = "mysql"

    def __init__(self, connection: dict[str, Any]) -> None:
        super().__init__(connection)
        self._conn_str = self._build_dsn(connection)
        self._pool = None

    @staticmethod
    def _build_dsn(conn: dict[str, Any]) -> str:
        return (
            f"mysql://{conn['user']}:{conn['password']}"
            f"@{conn['host']}:{conn.get('port', 3306)}/{conn['db']}"
        )

    async def test_connection(self) -> ConnectionResult:
        try:
            import aiomysql
        except ImportError:
            return ConnectionResult(
                connected=False,
                error_code="E_SYS_MISSING_DEP",
                error_message="缺少依赖: aiomysql",
            )

        try:
            pool = await aiomysql.create_pool(
                self._conn_str,
                autocommit=True,
                connect_timeout=10,
                minsize=1,
                maxsize=2,
            )
            self._pool = pool
        except Exception as e:
            err_msg = str(e).lower()
            if "access denied" in err_msg or "auth" in err_msg:
                err = datasource_auth("mysql")
                return ConnectionResult(False, error_code=err.code.value, error_message=err.message)
            if "timed out" in err_msg or "timeout" in err_msg:
                err = datasource_timeout("mysql", timeout_s=10)
                return ConnectionResult(False, error_code=err.code.value, error_message=err.message)
            return ConnectionResult(False, error_code="E_DS_UNKNOWN", error_message=str(e))

        # 验证只读权限
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    result = await cur.fetchone()
                    if not result or result[0] != 1:
                        return ConnectionResult(False, error_code="E_DS_INVALID", error_message="SELECT 1 failed")

                    # 尝试写操作，预期失败
                    try:
                        await cur.execute("CREATE TABLE _aios_write_probe (id INT)")
                        await cur.execute("DROP TABLE _aios_write_probe")
                        # 写成功 → 账号不是只读 → 拒绝
                        err = datasource_no_permission("mysql")
                        return ConnectionResult(
                            False, error_code=err.code.value, error_message=err.message
                        )
                    except Exception:
                        # 写失败 → 只读 → 通过
                        pass

            # 拉表元数据
            tables = await self.extract_schema()
            return ConnectionResult(connected=True, tables=tables)
        except Exception as e:
            return ConnectionResult(connected=False, error_code="E_DS_QUERY_FAILED", error_message=str(e))

    async def extract_schema(self) -> list[TableInfo]:
        if self._pool is None:
            return []
        sql = """
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_COMMENT, TABLE_ROWS
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME
        """
        cols_sql = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_COMMENT
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """

        db = self._conn["db"]
        tables: list[TableInfo] = []
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, (db,))
                rows = await cur.fetchall()
                for schema, name, comment, est_rows in rows:
                    await cur.execute(cols_sql, (db, name))
                    cols = await cur.fetchall()
                    fields = [
                        FieldInfo(
                            name=c[0],
                            data_type=c[1],
                            nullable=(c[2] == "YES"),
                            is_primary_key=(c[3] == "PRI"),
                            comment=c[4],
                        )
                        for c in cols
                    ]
                    tables.append(
                        TableInfo(
                            schema_name=schema,
                            table_name=name,
                            fields=fields,
                            estimated_rows=est_rows,
                            comment=comment,
                        )
                    )
        return tables

    async def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None