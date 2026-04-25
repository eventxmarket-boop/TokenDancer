from __future__ import annotations

import threading
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


_LATEST_PLUS_BRIDGE_RESULT: dict[str, Any] | None = None
_LATEST_PLUS_BRIDGE_STATUS: dict[str, Any] | None = None
_PLUS_BRIDGE_EVENTS: list[dict[str, Any]] = []
_LOCK = threading.Lock()


def store_plus_bridge_result(payload: dict[str, Any]) -> dict[str, Any]:
    record = deepcopy(payload)
    record["accepted"] = True
    record["received_at"] = datetime.now(timezone.utc).isoformat()

    with _LOCK:
        global _LATEST_PLUS_BRIDGE_RESULT
        global _LATEST_PLUS_BRIDGE_STATUS
        _LATEST_PLUS_BRIDGE_RESULT = record
        _LATEST_PLUS_BRIDGE_STATUS = {
            "updated_at": record["received_at"],
            "mode": "generate",
            "transport": record.get("transport", "persistent"),
            "stage": "uploaded" if record.get("source") else "captured",
            "message": "图片结果已接收",
            "prompt": record.get("prompt", ""),
            "prompt_length": len(str(record.get("prompt", ""))),
            "size": record.get("size", "unknown"),
            "quality": record.get("quality", "unknown"),
            "output_format": record.get("output_format", "png"),
            "model": record.get("model", "chatgpt-plus-bridge"),
            "page_url": "",
            "image_base64": record.get("image_base64", ""),
            "mime_type": record.get("mime_type", ""),
            "success": True,
            "error": None,
            "user_id": record.get("user_id"),
            "events": deepcopy(_PLUS_BRIDGE_EVENTS[-12:]),
        }

    return deepcopy(record)


def get_latest_plus_bridge_result() -> dict[str, Any] | None:
    with _LOCK:
        if _LATEST_PLUS_BRIDGE_RESULT is None:
            return None
        return deepcopy(_LATEST_PLUS_BRIDGE_RESULT)


def store_plus_bridge_event(payload: dict[str, Any]) -> dict[str, Any]:
    record = deepcopy(payload)
    record["accepted"] = True
    record["received_at"] = datetime.now(timezone.utc).isoformat()

    with _LOCK:
        global _LATEST_PLUS_BRIDGE_STATUS
        _PLUS_BRIDGE_EVENTS.append(record)
        _PLUS_BRIDGE_EVENTS[:] = _PLUS_BRIDGE_EVENTS[-20:]
        _LATEST_PLUS_BRIDGE_STATUS = {
            "updated_at": record["received_at"],
            "mode": record.get("mode", "generate"),
            "transport": record.get("transport", "persistent"),
            "stage": record.get("stage", "unknown"),
            "message": record.get("message", ""),
            "prompt": record.get("prompt", ""),
            "prompt_length": int(record.get("prompt_length", 0) or 0),
            "size": record.get("size", "unknown"),
            "quality": record.get("quality", "unknown"),
            "output_format": record.get("output_format", "png"),
            "model": record.get("model", "chatgpt-plus-bridge"),
            "page_url": record.get("page_url", ""),
            "image_base64": record.get("image_base64", ""),
            "mime_type": record.get("mime_type", ""),
            "success": record.get("success"),
            "error": record.get("error"),
            "user_id": record.get("user_id"),
            "events": deepcopy(_PLUS_BRIDGE_EVENTS),
        }

    return deepcopy(record)


def get_plus_bridge_status() -> dict[str, Any] | None:
    with _LOCK:
        if _LATEST_PLUS_BRIDGE_STATUS is None:
            return None
        return deepcopy(_LATEST_PLUS_BRIDGE_STATUS)
