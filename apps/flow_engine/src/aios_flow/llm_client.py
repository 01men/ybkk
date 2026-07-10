"""aios_flow.llm_client —— 统一 LLM 调用抽象（V6：支持本地 ollama + Anthropic 兼容云端 API）。"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger("aios_flow.llm_client")

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


def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    timeout: float = 60.0,
    temperature: float = 0.2,
) -> tuple[str, int]:
    """调 LLM，返回 (text, duration_ms)。"""
    provider = get_provider()
    model = model or get_model()
    start = time.time()
    if provider == "anthropic":
        text = _anthropic_chat(messages, model=model, timeout=timeout, temperature=temperature)
    else:
        text = _ollama_chat(messages, model=model, timeout=timeout)
    duration_ms = int((time.time() - start) * 1000)
    return text, duration_ms


def _ollama_chat(messages: list[dict[str, str]], *, model: str, timeout: float) -> str:
    url = get_ollama_url()
    try:
        r = httpx.post(
            f"{url}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=timeout,
        )
        r.raise_for_status()
        payload = r.json()
        return (
            payload.get("message", {}).get("content", "")
            or payload.get("response", "")
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("ollama chat failed: %s", e)
        return ""


def _extract_system_text(messages: list[dict[str, str]]) -> str:
    parts: list[str] = []
    for m in messages:
        if m.get("role") == "system":
            parts.append(m["content"])
    return "\n\n".join(parts)


def _to_anthropic_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    return [m for m in messages if m.get("role") != "system"]


def _anthropic_chat(
    messages: list[dict[str, str]], *, model: str, timeout: float, temperature: float
) -> str:
    base = get_anthropic_url()
    api_key = get_api_key()
    if not api_key:
        logger.warning("AIOS_LLM_API_KEY not set, anthropic call will likely fail")
    system_text = _extract_system_text(messages)
    body: dict[str, Any] = {
        "model": model,
        "max_tokens": 2048,
        "temperature": temperature,
        "messages": _to_anthropic_messages(messages),
    }
    if system_text:
        body["system"] = system_text
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
        logger.warning("anthropic chat failed: %s", e)
        return ""


__all__ = ["chat", "get_provider", "get_model"]
