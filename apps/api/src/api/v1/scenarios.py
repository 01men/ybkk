"""aios_api.api.v1.scenarios —— 场景模板 API（V1 列表 + 详情）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import get_session
from ...errors import AiosError, ErrorCode
from ...middleware.auth import CurrentUser
from ...models import Scenario

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", summary="列出场景模板")
async def list_scenarios(
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict]:
    result = await session.execute(select(Scenario).order_by(Scenario.key))
    return [
        {
            "id": s.id,
            "key": s.key,
            "name": s.name,
            "industry": s.industry,
            "description": s.description,
            "default_standard_keys": s.default_standard_keys,
            "flow_template": s.flow_template_json,
            "built_in": s.built_in,
        }
        for s in result.scalars().all()
    ]


@router.get("/{key}", summary="场景详情")
async def get_scenario(
    key: str,
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    result = await session.execute(select(Scenario).where(Scenario.key == key))
    s = result.scalar_one_or_none()
    if s is None:
        raise AiosError(ErrorCode.E_FLOW_NOT_FOUND, f"场景不存在: {key}", http_status=404)
    return {
        "id": s.id,
        "key": s.key,
        "name": s.name,
        "industry": s.industry,
        "description": s.description,
        "default_standard_keys": s.default_standard_keys,
        "flow_template": s.flow_template_json,
        "built_in": s.built_in,
    }
