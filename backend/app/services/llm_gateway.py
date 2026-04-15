from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


class LLMGatewayError(RuntimeError):
    pass


@dataclass(slots=True)
class LLMReply:
    content: str
    model: str
    usage: dict[str, int]
    latency_ms: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
        }


def _env_value(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else default


def _get_base_url() -> str:
    base_url = _env_value("LLM_BASE_URL", settings.LLM_BASE_URL or "")
    if not base_url:
        return "https://api.openai.com/v1"
    return base_url.rstrip("/")


def _get_api_key() -> str:
    return _env_value("LLM_API_KEY", settings.LLM_API_KEY or "")


def _get_model() -> str:
    model = _env_value("LLM_MODEL", settings.LLM_MODEL or "gpt-5.4-mini")
    return model or "gpt-5.4-mini"


def _get_temperature() -> float:
    raw = _env_value("LLM_TEMPERATURE", str(settings.LLM_TEMPERATURE))
    try:
        return float(raw)
    except ValueError as exc:
        raise LLMGatewayError(f"LLM_TEMPERATURE 配置无效: {raw!r}") from exc


def _get_max_tokens() -> int:
    raw = _env_value("LLM_MAX_TOKENS", str(settings.LLM_MAX_TOKENS))
    try:
        return int(raw)
    except ValueError as exc:
        raise LLMGatewayError(f"LLM_MAX_TOKENS 配置无效: {raw!r}") from exc


def _extract_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content.strip()
                if isinstance(content, list):
                    pieces: list[str] = []
                    for item in content:
                        if isinstance(item, dict):
                            text = item.get("text")
                            if isinstance(text, str):
                                pieces.append(text)
                    return "".join(pieces).strip()
            text = first_choice.get("text")
            if isinstance(text, str):
                return text.strip()
    raise LLMGatewayError("模型响应中缺少可解析的 content")


async def generate_reply(messages: list[dict[str, str]]) -> dict[str, Any]:
    api_key = _get_api_key()
    if not api_key:
        raise LLMGatewayError("当前模型服务不可用：LLM_API_KEY 未配置")

    base_url = _get_base_url()
    model = _get_model()
    temperature = _get_temperature()
    max_tokens = _get_max_tokens()
    endpoint = f"{base_url}/chat/completions"

    request_payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    started_at = time.perf_counter()
    timeout = httpx.Timeout(60.0, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(endpoint, headers=headers, json=request_payload)

    latency_ms = int((time.perf_counter() - started_at) * 1000)
    if response.status_code >= 400:
        detail = response.text.strip()
        raise LLMGatewayError(
            f"模型调用失败 ({response.status_code}): {detail or 'unknown error'}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise LLMGatewayError("模型响应不是有效 JSON") from exc

    usage_payload = payload.get("usage") if isinstance(payload, dict) else {}
    usage = {
        "prompt_tokens": int((usage_payload or {}).get("prompt_tokens") or 0),
        "completion_tokens": int((usage_payload or {}).get("completion_tokens") or 0),
        "total_tokens": int((usage_payload or {}).get("total_tokens") or 0),
    }

    return LLMReply(
        content=_extract_content(payload),
        model=str(payload.get("model") or model),
        usage=usage,
        latency_ms=latency_ms,
    ).as_dict()
