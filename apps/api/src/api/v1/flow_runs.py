"""aios_api.api.v1.flow_runs —— FlowRun 查询 API（V1）。"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import get_session
from ...errors import AiosError, ErrorCode
from ...middleware.auth import CurrentUser
from ...models import Flow, FlowRun

router = APIRouter(prefix="/flow-runs", tags=["flow-runs"])


class FlowRunResponse(BaseModel):
    id: str
    flow_id: str
    status: str
    trigger_type: str | None
    actor: str | None
    triggered_at: datetime
    finished_at: datetime | None
    step_results: dict | None
    output: dict | None


@router.get("/by-flow/{flow_id}", summary="列出某 Flow 的所有 Run")
async def list_runs_by_flow(
    flow_id: str,
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[FlowRunResponse]:
    result = await session.execute(
        select(FlowRun).where(FlowRun.flow_id == flow_id).order_by(FlowRun.triggered_at.desc())
    )
    return [
        FlowRunResponse(
            id=r.id,
            flow_id=r.flow_id,
            status=r.status.value,
            trigger_type=r.trigger_type,
            actor=r.actor,
            triggered_at=r.triggered_at,
            finished_at=r.finished_at,
            step_results=r.step_results,
            output=r.output_json,
        )
        for r in result.scalars().all()
    ]


@router.get("/{run_id}", response_model=FlowRunResponse, summary="FlowRun 详情")
async def get_run(
    run_id: str,
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FlowRunResponse:
    r = await session.get(FlowRun, run_id)
    if r is None:
        raise AiosError(ErrorCode.E_FLOW_NOT_FOUND, f"Run 不存在: {run_id}", http_status=404)
    return FlowRunResponse(
        id=r.id,
        flow_id=r.flow_id,
        status=r.status.value,
        trigger_type=r.trigger_type,
        actor=r.actor,
        triggered_at=r.triggered_at,
        finished_at=r.finished_at,
        step_results=r.step_results,
        output=r.output_json,
    )
