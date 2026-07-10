"""aios_ontology.llm_client —— 统一 LLM 调用抽象（V6：支持本地 ollama + Anthropic 兼容云端 API）。

与 apps/api/src/llm_client.py 同源（业务等价）。每个 app 各自一份以避免包依赖。
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger("aios_ontology.llm_client")

OLLAMA_DEFAULT_URL = "http://ollama:11434"
ANTHROPIC_DEFAULT_URL = "https://api.anthropic.com"


def get_provider() -> str:
    return os.getenv("AIOS_LLM_PROVIDER", "ollama").lower()


def get_ollama_url() -> str:
    return os.getenv("AIOS_LLM_URL", OLLAMA_DEFAULT_URL)


def get_anthropic_url() -> str:
    return os.getenv("AIOS_LLM_BASE_URL", ANTHROPIC_DEFAULT_URL).rstrip("/")


def get_api_key() -> str:
    return os.getenv("AIOS_LLM_API_KEY", "")


def get_model() -> str:
    return os.getenv("AIOS_LLM_MODEL", "qwen2.5:7b")


def generate(prompt: str, *, model: str | None = None, timeout: float = 60.0) -> str:
    """单轮 prompt 调 LLM，返回文本。"""
    provider = get_provider()
    model = model or get_model()
    if provider == "anthropic":
        return _anthropic_generate(prompt, model=model, timeout=timeout)
    return _ollama_generate(prompt, model=model, timeout=timeout)


def _ollama_generate(prompt: str, *, model: str, timeout: float) -> str:
    url = get_ollama_url()
    try:
        r = httpx.post(
            f"{url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json().get("response", "")
    except Exception as e:  # noqa: BLE001
        logger.warning("ollama generate failed: %s", e)
        return ""


def _anthropic_generate(prompt: str, *, model: str, timeout: float) -> str:
    base = get_anthropic_url()
    api_key = get_api_key()
    body: dict[str, Any] = {
        "model": model,
        "max_tokens": 2048,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "content-type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    try:
        r = httpx.post(
            f"{base}/v1/messages",
            json=body,
            headers=headers,
            timeout=timeout,
        )
        r.raise_for_status()
        payload = r.json()
        content_blocks = payload.get("content", [])
        parts: list[str] = []
        for block in content_blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    except Exception as e:  # noqa: BLE001
        logger.warning("anthropic generate failed: %s", e)
        return ""


__all__ = ["generate", "get_provider", "get_model"]
