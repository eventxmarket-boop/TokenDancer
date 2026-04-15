from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.services.llm_config_service import LLMConfigServiceError, resolve_llm_config


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


def strip_think_blocks(text: str) -> str:
    if not text:
        return text

    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<reasoning>.*?</reasoning>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<analysis>.*?</analysis>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


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


async def generate_reply(
    messages: list[dict[str, str]],
    db: Session | None = None,
) -> dict[str, Any]:
    try:
        resolved_config = resolve_llm_config(db)
    except LLMConfigServiceError as exc:
        raise LLMGatewayError(str(exc)) from exc

    api_key = resolved_config.api_key
    if not api_key:
        raise LLMGatewayError("当前模型服务不可用：未配置启用的大模型 API Key")

    base_url = resolved_config.base_url.rstrip("/")
    model = resolved_config.model_name
    temperature = resolved_config.temperature
    max_tokens = resolved_config.max_tokens
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
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(endpoint, headers=headers, json=request_payload)
    except httpx.HTTPError as exc:
        raise LLMGatewayError(f"模型请求失败: {exc}") from exc

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

    raw_content = _extract_content(payload)
    clean_content = strip_think_blocks(raw_content)

    return LLMReply(
        content=clean_content,
        model=str(payload.get("model") or model),
        usage=usage,
        latency_ms=latency_ms,
    ).as_dict()
