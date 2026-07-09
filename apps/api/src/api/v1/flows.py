"""aios_api.api.v1.flows —— 流程管理 API（V1 列表 / 创建 / 详情 / 触发）。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Literal

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...db import get_session
from ...errors import AiosError, ErrorCode
from ...middleware.auth import CurrentUser
from ...models import Flow, FlowStatus

router = APIRouter(prefix="/flows", tags=["flows"])


# -----------------------------------------------------------------------------
# Pydantic
# -----------------------------------------------------------------------------


class CreateFlowRequest(BaseModel):
    scenario_id: str = Field(..., min_length=1)
    datasource_bindings: dict = Field(default_factory=dict)
    standard_overrides: dict = Field(default_factory=dict)
    trigger_type: Literal["manual", "schedule", "ontology_event"] = "manual"
    trigger_config: dict = Field(default_factory=dict)


class FlowResponse(BaseModel):
    id: str
    scenario_id: str
    status: str
    trigger_type: str | None
    trigger_config: dict | None
    created_by: str
    created_at: datetime


# -----------------------------------------------------------------------------
# 端点
# -----------------------------------------------------------------------------


@router.get("", summary="列出 Flow")
async def list_flows(
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[FlowResponse]:
    result = await session.execute(select(Flow).order_by(Flow.created_at.desc()))
    return [
        FlowResponse(
            id=f.id,
            scenario_id=f.scenario_id,
            status=f.status.value,
            trigger_type=f.trigger_type,
            trigger_config=f.trigger_config,
            created_by=f.created_by,
            created_at=f.created_at,
        )
        for f in result.scalars().all()
    ]


@router.post("", response_model=FlowResponse, status_code=201, summary="创建 Flow")
async def create_flow(
    body: CreateFlowRequest,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FlowResponse:
    f = Flow(
        id=str(uuid.uuid4()),
        scenario_id=body.scenario_id,
        datasource_bindings_json=body.datasource_bindings,
        standard_overrides_json=body.standard_overrides,
        trigger_type=body.trigger_type,
        trigger_config=body.trigger_config,
        status=FlowStatus.ACTIVE if body.trigger_type == "manual" else FlowStatus.DRAFT,
        created_by=user["username"],
    )
    session.add(f)
    await session.commit()
    await session.refresh(f)
    return FlowResponse(
        id=f.id,
        scenario_id=f.scenario_id,
        status=f.status.value,
        trigger_type=f.trigger_type,
        trigger_config=f.trigger_config,
        created_by=f.created_by,
        created_at=f.created_at,
    )


@router.get("/{flow_id}", response_model=FlowResponse, summary="Flow 详情")
async def get_flow(
    flow_id: str,
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FlowResponse:
    f = await session.get(Flow, flow_id)
    if f is None:
        raise AiosError(ErrorCode.E_FLOW_NOT_FOUND, f"Flow 不存在: {flow_id}", http_status=404)
    return FlowResponse(
        id=f.id,
        scenario_id=f.scenario_id,
        status=f.status.value,
        trigger_type=f.trigger_type,
        trigger_config=f.trigger_config,
        created_by=f.created_by,
        created_at=f.created_at,
    )


@router.post("/{flow_id}/trigger", summary="手动触发 Flow")
async def trigger_flow(
    flow_id: str,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    f = await session.get(Flow, flow_id)
    if f is None:
        raise AiosError(ErrorCode.E_FLOW_NOT_FOUND, f"Flow 不存在: {flow_id}", http_status=404)
    if f.trigger_type != "manual":
        raise AiosError(
            ErrorCode.E_FLOW_TRIGGER_FAILED,
            f"非 manual 类型的 Flow 不能手动触发: {f.trigger_type}",
            http_status=400,
        )

    # 通知 flow_engine 启动 Temporal workflow
    settings = get_settings()
    flow_engine_url = getattr(settings, "flow_engine_url", "http://flow-engine:8081")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{flow_engine_url}/workflows/start",
                json={"flow_id": f.id, "scenario_id": f.scenario_id, "actor": user["username"]},
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        raise AiosError(
            ErrorCode.E_FLOW_TRIGGER_FAILED,
            f"调用 flow_engine 失败: {e}",
            http_status=502,
        ) from e
