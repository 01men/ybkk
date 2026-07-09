"""aios_flow.activities.llm_judge —— V2 LLM 判断 activity。

设计：场景里某些 step 需要"语义判断"（如：质检描述是否描述了缺陷、来料是否异常）。
V2 把这种判断抽成 LLM judge activity，统一通过 AIOS_LLM_URL 调 Ollama。
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger("aios_flow.llm_judge")


@dataclass
class LLMJudgeInput:
    """LLM judge 输入。

    - prompt: 完整 prompt 模板
    - context: 业务上下文（dict，会 JSON 序列化后塞 prompt）
    - expected_schema: 期望返回 JSON 的 key 列表（用于校验）
    - provider: 预留多 provider（V2 仅 qwen-local）
    - model: 模型名（默认 qwen2.5:7b）
    - actor: 调用人（用于审计）
    - run_id: 关联 flow run（用于审计）
    """

    prompt: str
    context: dict[str, Any] = field(default_factory=dict)
    expected_schema: list[str] = field(default_factory=list)
    provider: str = "qwen-local"
    model: str = "qwen2.5:7b"
    actor: str = "system"
    run_id: str = ""


@dataclass
class LLMJudgeResult:
    """LLM judge 输出。

    - decision: 布尔（True=匹配/异常, False=不匹配/正常）
    - confidence: 0-1 置信度
    - reasoning: LLM 给的理由
    - raw_response: 原始响应
    - duration_ms: 调用耗时
    - llm_call_id: 写入 llm_calls 表的 ID（V2 占位生成）
    """

    decision: bool
    confidence: float
    reasoning: str
    raw_response: str
    duration_ms: int
    llm_call_id: str = ""


_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


def _extract_json(text: str) -> dict:
    """从 LLM 响应里抠 JSON。容忍 markdown 围栏、前后说明。"""
    if not text:
        return {}
    # 优先匹配 ```json ... ``` 围栏
    fence = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass
    # 其次匹配首个 {...} 块
    m = _JSON_BLOCK_RE.search(text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    # 兜底：整段当 JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _build_full_prompt(template: str, context: dict[str, Any]) -> str:
    """把 context 拼到 prompt 末尾。"""
    ctx_str = json.dumps(context, ensure_ascii=False, indent=2)
    return f"{template}\n\n【业务上下文】\n{ctx_str}\n\n【输出要求】\n严格返回 JSON 对象，键: decision (bool), confidence (0-1), reasoning (str)。"


def _llm_call(ollama_url: str, model: str, prompt: str, timeout: float = 60.0) -> tuple[str, int]:
    """调 Ollama /api/generate。返回 (response_text, duration_ms)。"""
    start = time.time()
    with httpx.Client(timeout=timeout) as client:
        r = client.post(
            f"{ollama_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
        )
        r.raise_for_status()
        text = r.json().get("response", "")
    duration_ms = int((time.time() - start) * 1000)
    return text, duration_ms


def _gen_call_id(prompt: str, response: str) -> str:
    """生成稳定 llm_call_id（V2 不落库，只做占位标识）。"""
    h = hashlib.sha256(f"{prompt}|{response}".encode("utf-8")).hexdigest()[:16]
    return f"llm_{h}"


async def llm_judge(input: LLMJudgeInput) -> LLMJudgeResult:
    """LLM judge 核心实现。

    调用链：
      1. 拼 prompt + context
      2. 调 Ollama
      3. 抠 JSON
      4. 校验 expected_schema（缺失则降级）
      5. 返回 decision/confidence/reasoning
    """
    ollama_url = os.getenv("AIOS_LLM_URL", "http://ollama:11434")
    full_prompt = _build_full_prompt(input.prompt, input.context)

    try:
        text, duration_ms = _llm_call(ollama_url, input.model, full_prompt)
    except Exception as e:  # noqa: BLE001 — 任何 LLM 调用异常都保守降级
        logger.warning("llm call failed: %s", e)
        # 失败时保守返回 False（不触发）
        return LLMJudgeResult(
            decision=False,
            confidence=0.0,
            reasoning=f"[llm_call_error] {type(e).__name__}: {e}",
            raw_response="",
            duration_ms=0,
        )

    parsed = _extract_json(text)
    decision = bool(parsed.get("decision", False))
    try:
        confidence = float(parsed.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    reasoning = str(parsed.get("reasoning", ""))[:1000]

    # 校验 expected_schema
    if input.expected_schema:
        missing = [k for k in input.expected_schema if k not in parsed]
        if missing:
            logger.info("llm response missing expected keys: %s", missing)
            confidence = min(confidence, 0.5)  # 降权

    return LLMJudgeResult(
        decision=decision,
        confidence=confidence,
        reasoning=reasoning,
        raw_response=text[:2000],
        duration_ms=duration_ms,
        llm_call_id=_gen_call_id(full_prompt, text),
    )


# --- V2 场景内置 judge 模板 ---------------------------------------------------

JUDGE_TEMPLATES: dict[str, str] = {
    "quality_defect": (
        "你是质检分析师。根据下列质检描述，判断是否存在缺陷（裂纹、变形、污渍、尺寸超差、"
        "功能异常、材质不符等）。只在确实异常时返回 decision=true。"
    ),
    "inbound_anomaly": (
        "你是来料检验员。根据下列来料数据，判断是否异常：库存不足、超量、批次过期、"
        "供应商评级下滑、价格异常波动等。只在确实异常时返回 decision=true。"
    ),
    "equipment_alert": (
        "你是设备维护工程师。根据下列设备运行数据（温度/振动/电流/运行时长/最近保养记录），"
        "判断是否存在保养预警或故障隐患。只在确实异常时返回 decision=true。"
    ),
}


def get_template(key: str) -> str:
    return JUDGE_TEMPLATES.get(key, JUDGE_TEMPLATES["equipment_alert"])
