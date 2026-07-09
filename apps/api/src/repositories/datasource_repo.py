"""数据源仓储（仅写 PostgreSQL；连接外部数据源在 service 层）。"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Datasource, DatasourceStatus


class DatasourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self, type_: str, connection_json_encrypted: str
    ) -> Datasource:
        ds = Datasource(
            id=f"ds-{uuid.uuid4().hex[:16]}",
            type=type_,
            connection_json_encrypted=connection_json_encrypted,
            status=DatasourceStatus.PENDING,
        )
        self._s.add(ds)
        await self._s.flush()
        return ds

    async def get(self, datasource_id: str) -> Datasource | None:
        result = await self._s.execute(
            select(Datasource).where(Datasource.id == datasource_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self, datasource_id: str, status: DatasourceStatus
    ) -> None:
        ds = await self.get(datasource_id)
        if ds is None:
            return
        ds.status = status
        ds.last_check_at = datetime.now(UTC)
        await self._s.flush()

    async def list_all(self) -> list[Datasource]:
        result = await self._s.execute(
            select(Datasource).order_by(Datasource.created_at.desc())
        )
        return list(result.scalars().all())