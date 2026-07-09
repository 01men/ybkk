"""aios_api.api.v1.internal —— 内部服务调用接口（worker / scheduler 回调）。"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...audit_util import write_audit
from ...db import get_session
from ...middleware.auth import CurrentUser
from ...models import Flow, FlowRun, FlowRunStatus

router = APIRouter(prefix="/internal", tags=["internal"])


class RecordRunRequest(BaseModel):
    run_id: str
    flow_id: str
    status: str  # running / success / failed
    trigger_type: str | None = None
    actor: str | None = None
    step_results: list[dict] | None = None


@router.post("/flow-runs/record", summary="worker 回调：记录 FlowRun 状态")
async def record_flow_run(
    body: RecordRunRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """由 flow_engine 在 workflow 开始/结束时回调。"""
    f = await session.get(Flow, body.flow_id)
    if f is None:
        return {"ok": False, "reason": "flow_not_found"}

    # 查现有 run
    result = await session.execute(
        select(FlowRun).where(FlowRun.id == body.run_id)
    )
    run = result.scalar_one_or_none()

    if run is None:
        run = FlowRun(
            id=body.run_id,
            flow_id=body.flow_id,
            status=FlowRunStatus(body.status),
            trigger_type=body.trigger_type or "manual",
            actor=body.actor or "system",
            step_results={"steps": body.step_results or []},
        )
        session.add(run)
    else:
        run.status = FlowRunStatus(body.status)
        run.step_results = {"steps": body.step_results or []}
        if body.status in ("success", "failed", "cancelled"):
            run.finished_at = datetime.now(timezone.utc)

    await session.commit()

    # 写审计
    await write_audit(
        session,
        actor=body.actor or "system",
        action=f"flow_run.{body.status}",
        flow_id=body.flow_id,
        run_id=body.run_id,
        payload={"step_count": len(body.step_results or [])},
    )
    await session.commit()

    return {"ok": True, "run_id": body.run_id, "status": body.status}


@router.get("/flows/schedule-eligible", summary="列出所有 schedule 类型的 Flow")
async def schedule_eligible_flows(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict]:
    result = await session.execute(
        select(Flow).where(Flow.trigger_type == "schedule")
    )
    out = []
    for f in result.scalars().all():
        out.append(
            {
                "id": f.id,
                "scenario_id": f.scenario_id,
                "trigger_type": f.trigger_type,
                "trigger_config": f.trigger_config,
                "datasource_bindings": f.datasource_bindings_json,
                "standard_overrides": f.standard_overrides_json,
            }
        )
    return out
