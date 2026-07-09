"""aios_api.audit_util —— 写审计的工具函数（V1 worker 回调用）。"""
from __future__ import annotations

import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditLog


async def write_audit(
    session: AsyncSession,
    *,
    actor: str,
    action: str,
    datasource_id: str | None = None,
    standard_ref: str | None = None,
    flow_id: str | None = None,
    run_id: str | None = None,
    payload: dict | None = None,
) -> AuditLog:
    """计算 hash_chain（前一条 hash + 本条内容）→ 写入 audit_log。"""
    payload = payload or {}
    # 找最后一条
    from sqlalchemy import select

    result = await session.execute(
        select(AuditLog).order_by(AuditLog.id.desc()).limit(1)
    )
    last = result.scalar_one_or_none()
    prev_hash = last.hash_chain if last else "0" * 64

    # 拿 server 端 ts 不可靠（lazy create）；用本地 UTC ISO
    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc)

    h = hashlib.sha256()
    h.update(prev_hash.encode("ascii"))
    h.update(ts.isoformat().encode("utf-8"))
    h.update(actor.encode("utf-8"))
    h.update(action.encode("utf-8"))
    h.update((datasource_id or "").encode("utf-8"))
    h.update((standard_ref or "").encode("utf-8"))
    h.update((flow_id or "").encode("utf-8"))
    h.update((run_id or "").encode("utf-8"))
    h.update(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    chain = h.hexdigest()

    row = AuditLog(
        ts=ts,
        actor=actor,
        action=action,
        datasource_id=datasource_id,
        standard_ref=standard_ref,
        flow_id=flow_id,
        run_id=run_id,
        payload_json=payload,
        hash_chain=chain,
    )
    session.add(row)
    return row
