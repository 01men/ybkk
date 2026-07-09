"""aios_api.api.v1.llm —— LLM 用量 + 测试 API（V2）。"""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import get_session
from ...middleware.auth import CurrentUser
from ...models import LLMCall

router = APIRouter(prefix="/llm", tags=["llm"])


class UsageResponse(BaseModel):
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    by_provider: dict[str, dict]


class TestRequest(BaseModel):
    prompt: str
    provider: str = "qwen-local"


class TestResponse(BaseModel):
    response: str
    duration_ms: int


@router.get("/usage", response_model=UsageResponse, summary="LLM 用量统计")
async def get_usage(
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UsageResponse:
    result = await session.execute(
        select(
            LLMCall.provider,
            func.count(LLMCall.id).label("calls"),
            func.coalesce(func.sum(LLMCall.input_tokens), 0).label("in_tok"),
            func.coalesce(func.sum(LLMCall.output_tokens), 0).label("out_tok"),
            func.coalesce(func.sum(LLMCall.cost_usd), 0.0).label("cost"),
        ).group_by(LLMCall.provider)
    )
    by_provider: dict[str, dict] = {}
    total_calls = 0
    total_in = 0
    total_out = 0
    total_cost = 0.0
    for row in result.all():
        by_provider[row.provider] = {
            "calls": int(row.calls),
            "input_tokens": int(row.in_tok),
            "output_tokens": int(row.out_tok),
            "cost_usd": float(row.cost),
        }
        total_calls += int(row.calls)
        total_in += int(row.in_tok)
        total_out += int(row.out_tok)
        total_cost += float(row.cost)
    return UsageResponse(
        total_calls=total_calls,
        total_input_tokens=total_in,
        total_output_tokens=total_out,
        total_cost_usd=round(total_cost, 4),
        by_provider=by_provider,
    )


@router.post("/test", response_model=TestResponse, summary="测试 LLM 连通")
async def test_llm(body: TestRequest, user: CurrentUser) -> TestResponse:
    """V2 简化：只测本地 Qwen。"""
    ollama_url = os.getenv("AIOS_LLM_URL", "http://ollama:11434")
    import time

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{ollama_url}/api/generate",
                json={"model": "qwen2.5:7b", "prompt": body.prompt, "stream": False},
            )
            r.raise_for_status()
            response_text = r.json().get("response", "")
    except httpx.HTTPError as e:
        return TestResponse(response=f"[error] {e}", duration_ms=int((time.time() - start) * 1000))
    duration_ms = int((time.time() - start) * 1000)

    # 记调用
    # V2 简化：仅在成功时记
    return TestResponse(response=response_text, duration_ms=duration_ms)
