"""aios_api.api.v1.audits —— 审计日志查询 API（V1）。"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import get_session
from ...middleware.auth import CurrentUser
from ...models import AuditLog

router = APIRouter(prefix="/audits", tags=["audits"])


class AuditEntry(BaseModel):
    id: int
    ts: datetime
    actor: str
    action: str
    datasource_id: str | None
    standard_ref: str | None
    flow_id: str | None
    run_id: str | None
    payload: dict
    hash_chain: str


class ChainVerifyResult(BaseModel):
    valid: bool
    broken_at: int | None
    total: int


@router.get("", summary="列出审计日志")
async def list_audits(
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 200,
) -> list[AuditEntry]:
    limit = max(1, min(limit, 2000))
    result = await session.execute(
        select(AuditLog).order_by(AuditLog.ts.desc()).limit(limit)
    )
    return [
        AuditEntry(
            id=row.id,
            ts=row.ts,
            actor=row.actor,
            action=row.action,
            datasource_id=row.datasource_id,
            standard_ref=row.standard_ref,
            flow_id=row.flow_id,
            run_id=row.run_id,
            payload=row.payload_json,
            hash_chain=row.hash_chain,
        )
        for row in result.scalars().all()
    ]


@router.get("/verify", response_model=ChainVerifyResult, summary="校验哈希链完整性")
async def verify_chain(
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ChainVerifyResult:
    """读全部 audit_log，按 ts 升序重新计算 sha256(prev_hash + content)，比对。"""
    import hashlib
    import json

    result = await session.execute(select(AuditLog).order_by(AuditLog.ts.asc(), AuditLog.id.asc()))
    rows = list(result.scalars().all())
    prev = "0" * 64
    for i, r in enumerate(rows):
        h = hashlib.sha256()
        h.update(prev.encode("ascii"))
        h.update(r.ts.isoformat().encode("utf-8"))
        h.update(r.actor.encode("utf-8"))
        h.update(r.action.encode("utf-8"))
        h.update((r.datasource_id or "").encode("utf-8"))
        h.update((r.standard_ref or "").encode("utf-8"))
        h.update((r.flow_id or "").encode("utf-8"))
        h.update((r.run_id or "").encode("utf-8"))
        h.update(json.dumps(r.payload_json, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        expected = h.hexdigest()
        if expected != r.hash_chain:
            return ChainVerifyResult(valid=False, broken_at=i, total=len(rows))
        prev = r.hash_chain
    return ChainVerifyResult(valid=True, broken_at=None, total=len(rows))
