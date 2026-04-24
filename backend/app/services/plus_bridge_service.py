from __future__ import annotations

import threading
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


_LATEST_PLUS_BRIDGE_RESULT: dict[str, Any] | None = None
_LOCK = threading.Lock()


def store_plus_bridge_result(payload: dict[str, Any]) -> dict[str, Any]:
    record = deepcopy(payload)
    record["accepted"] = True
    record["received_at"] = datetime.now(timezone.utc).isoformat()

    with _LOCK:
        global _LATEST_PLUS_BRIDGE_RESULT
        _LATEST_PLUS_BRIDGE_RESULT = record

    return deepcopy(record)


def get_latest_plus_bridge_result() -> dict[str, Any] | None:
    with _LOCK:
        if _LATEST_PLUS_BRIDGE_RESULT is None:
            return None
        return deepcopy(_LATEST_PLUS_BRIDGE_RESULT)
