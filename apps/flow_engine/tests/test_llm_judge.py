"""LLM judge activity 单测。"""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from aios_flow.activities.llm_judge import (
    LLMJudgeInput,
    _extract_json,
    _build_full_prompt,
    _gen_call_id,
    get_template,
    llm_judge,
)


# ---- _extract_json -----------------------------------------------------------


def test_extract_json_plain():
    assert _extract_json('{"decision": true, "confidence": 0.9}') == {
        "decision": True,
        "confidence": 0.9,
    }


def test_extract_json_markdown_fence():
    text = "下面是判断：\n```json\n{\"decision\": false, \"confidence\": 0.7}\n```\n完毕"
    assert _extract_json(text) == {"decision": False, "confidence": 0.7}


def test_extract_json_embedded():
    text = '分析：{"decision": true, "reasoning": "ok", "confidence": 0.8} 以上。'
    parsed = _extract_json(text)
    assert parsed["decision"] is True
    assert parsed["confidence"] == 0.8


def test_extract_json_invalid():
    assert _extract_json("not json at all") == {}
    assert _extract_json("") == {}


# ---- _build_full_prompt ------------------------------------------------------


def test_build_full_prompt_includes_context():
    template = "判断质量"
    ctx = {"material": "A001", "qty": 100}
    p = _build_full_prompt(template, ctx)
    assert "判断质量" in p
    assert '"material": "A001"' in p
    assert "decision" in p
    assert "confidence" in p


# ---- _gen_call_id ------------------------------------------------------------


def test_gen_call_id_stable():
    a = _gen_call_id("p", "r")
    b = _gen_call_id("p", "r")
    assert a == b
    assert a.startswith("llm_")
    assert len(a) == 20  # llm_ + 16


def test_gen_call_id_differs_on_change():
    assert _gen_call_id("p1", "r") != _gen_call_id("p2", "r")


# ---- judge templates ---------------------------------------------------------


def test_get_template_known_keys():
    for k in ("quality_defect", "inbound_anomaly", "equipment_alert"):
        assert isinstance(get_template(k), str)
        assert len(get_template(k)) > 0


def test_get_template_unknown_falls_back():
    assert get_template("nonsense") == get_template("equipment_alert")


# ---- llm_judge 核心（mock httpx） --------------------------------------------


def _mock_httpx_response(text: str):
    """构造一个 mock 出来的 httpx Response 对象。"""
    class _Resp:
        def __init__(self, payload: dict):
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._payload

    return _Resp({"response": text})


@pytest.mark.asyncio
async def test_llm_judge_decision_true():
    payload = json.dumps(
        {"decision": True, "confidence": 0.92, "reasoning": "明显异常"}
    )
    with patch("aios_flow.activities.llm_judge.httpx.Client") as MC:
        MC.return_value.__enter__.return_value.post.return_value = _mock_httpx_response(
            payload
        )
        result = await llm_judge(
            LLMJudgeInput(
                prompt="judge",
                context={"k": "v"},
                expected_schema=["decision", "confidence", "reasoning"],
            )
        )
    assert result.decision is True
    assert 0.9 < result.confidence <= 1.0
    assert "明显异常" in result.reasoning
    assert result.duration_ms >= 0
    assert result.llm_call_id.startswith("llm_")


@pytest.mark.asyncio
async def test_llm_judge_decision_false():
    payload = json.dumps({"decision": False, "confidence": 0.3, "reasoning": "ok"})
    with patch("aios_flow.activities.llm_judge.httpx.Client") as MC:
        MC.return_value.__enter__.return_value.post.return_value = _mock_httpx_response(
            payload
        )
        result = await llm_judge(LLMJudgeInput(prompt="judge", context={}))
    assert result.decision is False
    assert result.confidence == pytest.approx(0.3)


@pytest.mark.asyncio
async def test_llm_judge_missing_keys_downgrades_confidence():
    # 缺 reasoning
    payload = json.dumps({"decision": True, "confidence": 0.95})
    with patch("aios_flow.activities.llm_judge.httpx.Client") as MC:
        MC.return_value.__enter__.return_value.post.return_value = _mock_httpx_response(
            payload
        )
        result = await llm_judge(
            LLMJudgeInput(
                prompt="judge",
                context={},
                expected_schema=["decision", "confidence", "reasoning"],
            )
        )
    assert result.decision is True
    assert result.confidence <= 0.5  # 降权


@pytest.mark.asyncio
async def test_llm_judge_invalid_json_safe_default():
    with patch("aios_flow.activities.llm_judge.httpx.Client") as MC:
        MC.return_value.__enter__.return_value.post.return_value = _mock_httpx_response(
            "garbage"
        )
        result = await llm_judge(LLMJudgeInput(prompt="judge", context={}))
    assert result.decision is False
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_llm_judge_http_error_safe_default():
    with patch("aios_flow.activities.llm_judge.httpx.Client") as MC:
        MC.return_value.__enter__.return_value.post.side_effect = RuntimeError(
            "connection refused"
        )
        result = await llm_judge(LLMJudgeInput(prompt="judge", context={}))
    assert result.decision is False
    assert "[llm_call_error]" in result.reasoning
    assert result.duration_ms == 0


@pytest.mark.asyncio
async def test_llm_judge_markdown_fence_response():
    payload = (
        "好的，我的判断：\n```json\n"
        '{"decision": true, "confidence": 0.88, "reasoning": "fence path"}\n```'
    )
    with patch("aios_flow.activities.llm_judge.httpx.Client") as MC:
        MC.return_value.__enter__.return_value.post.return_value = _mock_httpx_response(
            payload
        )
        result = await llm_judge(LLMJudgeInput(prompt="judge", context={}))
    assert result.decision is True
    assert "fence path" in result.reasoning
