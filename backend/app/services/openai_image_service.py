from __future__ import annotations

import time
from typing import Any

from app.core.config import settings


class OpenAIImageServiceError(RuntimeError):
    pass


ALLOWED_IMAGE_SIZES = {"1024x1024", "1024x1536", "1536x1024", "auto"}
ALLOWED_IMAGE_QUALITIES = {"low", "medium", "high", "auto"}
ALLOWED_IMAGE_FORMATS = {"png", "webp", "jpeg"}

MIME_BY_FORMAT = {
    "png": "image/png",
    "webp": "image/webp",
    "jpeg": "image/jpeg",
}


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _validate_options(size: str, quality: str, output_format: str) -> None:
    if size not in ALLOWED_IMAGE_SIZES:
        raise ValueError(f"不支持的尺寸：{size}")
    if quality not in ALLOWED_IMAGE_QUALITIES:
        raise ValueError(f"不支持的质量：{quality}")
    if output_format not in ALLOWED_IMAGE_FORMATS:
        raise ValueError(f"不支持的格式：{output_format}")


def _build_client():
    api_key = _normalize_text(settings.OPENAI_API_KEY)
    if not api_key:
        raise OpenAIImageServiceError("当前模型服务不可用：未配置 OPENAI_API_KEY")

    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - runtime dependency guard
        raise OpenAIImageServiceError("当前模型服务不可用：OpenAI SDK 未安装") from exc

    return OpenAI(api_key=api_key)


def _extract_image_base64(result: Any) -> str:
    data = getattr(result, "data", None)
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            b64_json = first.get("b64_json")
            if isinstance(b64_json, str) and b64_json.strip():
                return b64_json.strip()
        else:
            b64_json = getattr(first, "b64_json", "")
            if isinstance(b64_json, str) and b64_json.strip():
                return b64_json.strip()
    raise OpenAIImageServiceError("模型响应中缺少图片数据")


def generate_image_base64(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
    output_format: str = "png",
    *,
    user_id: str | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    prompt_text = _normalize_text(prompt)
    _validate_options(size, quality, output_format)
    if len(prompt_text) < 3:
        raise ValueError("提示词至少需要 3 个字符")
    if len(prompt_text) > 4000:
        raise ValueError("提示词不能超过 4000 个字符")

    openai_client = client or _build_client()
    request_kwargs = {
        "model": settings.OPENAI_IMAGE_MODEL,
        "prompt": prompt_text,
        "size": size,
        "quality": quality,
        "output_format": output_format,
    }
    if user_id:
        request_kwargs["user"] = user_id

    try:
        result = openai_client.images.generate(**request_kwargs)
    except OpenAIImageServiceError:
        raise
    except Exception as exc:  # pragma: no cover - network/runtime guard
        raise OpenAIImageServiceError(f"图片生成失败：{exc}") from exc

    image_base64 = _extract_image_base64(result)
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)

    return {
        "image_base64": image_base64,
        "mime_type": MIME_BY_FORMAT.get(output_format, "image/png"),
        "model": settings.OPENAI_IMAGE_MODEL,
        "size": size,
        "quality": quality,
        "output_format": output_format,
        "elapsed_ms": elapsed_ms,
    }
