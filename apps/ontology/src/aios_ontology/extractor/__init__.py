"""aios_ontology.extractor —— LLM 驱动的实体 / 关系抽取。"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger("aios_ontology.extractor")


# -----------------------------------------------------------------------------
# Prompt 模板（V2 简化版：JSON mode + few-shot）
# -----------------------------------------------------------------------------


ENTITY_PROMPT = """你是制造业业务分析师。从下面文本中抽取所有"实体"。

支持的实体类型：Material / Supplier / Warehouse / Equipment / Order / Process / ProcessStep / BusinessRule / Role

每条实体输出 JSON：
{
  "kind": "Material",
  "external_id": "M001",  // 如果文本里有编号；否则自动生成
  "code": "M001",  // 业务编号
  "name": "螺栓 M8",
  "props": { "spec": "M8x30", "safety_stock": 100 }
}

仅返回 JSON 数组，不要解释。

文本：
{text}
"""

RELATION_PROMPT = """你是制造业业务分析师。从下面已抽取的实体列表中，识别实体之间的"关系"。

支持的关系类型：
- Material -SUPPLIED_BY-> Supplier
- Material -STORED_IN-> Warehouse
- Equipment -MAINTAINED_BY-> Role
- Process -HAS_STEP-> ProcessStep
- ProcessStep -NEXT-> ProcessStep
- Order -USES_MATERIAL-> Material
- Order -PRODUCED_BY-> Equipment
- Material -CRITICAL_TO-> Process
- BusinessRule -DEFINES-> DeliveryStandard

每条关系输出 JSON：
{ "from": "<external_id>", "type": "SUPPLIED_BY", "to": "<external_id>" }

仅返回 JSON 数组。

实体：
{entities_json}
"""


def _llm_call(prompt: str, model: str = "qwen2.5:7b") -> str:
    """调本地 Ollama / Qwen。V2 简化：只走本地。"""
    ollama_url = os.getenv("AIOS_LLM_URL", "http://ollama:11434")
    try:
        r = httpx.post(
            f"{ollama_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
            timeout=60.0,
        )
        r.raise_for_status()
        return r.json().get("response", "[]")
    except Exception as e:  # noqa: BLE001
        logger.warning("LLM call failed: %s, fallback to []", e)
        return "[]"


def _safe_json_array(text: str) -> list[dict]:
    """从 LLM 响应里抠 JSON 数组。"""
    # 找到第一个 [ 和最后一个 ]
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []


def extract_entities(text: str) -> list[dict[str, Any]]:
    """LLM 实体抽取。"""
    prompt = ENTITY_PROMPT.format(text=text[:4000])
    raw = _llm_call(prompt)
    return _safe_json_array(raw)


def extract_relations(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """LLM 关系抽取。"""
    prompt = RELATION_PROMPT.format(entities_json=json.dumps(entities, ensure_ascii=False)[:4000])
    raw = _llm_call(prompt)
    return _safe_json_array(raw)


__all__ = ["extract_entities", "extract_relations"]
