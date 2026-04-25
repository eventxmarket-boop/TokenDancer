#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


DEFAULT_STATUS_URL = "http://127.0.0.1:8011/persona-api/image-lab/bridge/status"
DEFAULT_BASE_URL = "http://127.0.0.1:8011"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "qclaw side bridge-status probe. "
            "Read-only test helper: fetch /persona-api/image-lab/bridge/status and print a concise summary."
        )
    )
    parser.add_argument(
        "--url",
        default=os.getenv("QCLAW_IMAGE_BRIDGE_STATUS_URL")
        or os.getenv("IMAGE_BRIDGE_STATUS_URL")
        or DEFAULT_STATUS_URL,
        help="Bridge status endpoint to query.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("QCLAW_IMAGE_BRIDGE_BASE_URL") or os.getenv("IMAGE_BRIDGE_BASE_URL") or DEFAULT_BASE_URL,
        help="Base URL used when --url is relative (starts with /).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("QCLAW_IMAGE_BRIDGE_TIMEOUT_SECONDS", "10")),
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the raw payload as formatted JSON after the summary.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Poll the endpoint repeatedly until interrupted.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=float(os.getenv("QCLAW_IMAGE_BRIDGE_POLL_SECONDS", "3")),
        help="Polling interval used with --watch.",
    )
    return parser


def fetch_status(url: str, timeout: float) -> dict[str, Any] | None:
    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace").strip()
    if not raw:
        return None
    data = json.loads(raw)
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError(f"Unexpected payload type: {type(data).__name__}")
    return data


def resolve_url(url: str, base_url: str) -> str:
    stripped = url.strip()
    if stripped.startswith("/"):
        return urljoin(base_url.rstrip("/") + "/", stripped.lstrip("/"))
    return stripped


def summarize(payload: dict[str, Any] | None, url: str) -> str:
    if payload is None:
        return "\n".join(
            [
                "QCLAW_IMAGE_BRIDGE_STATUS",
                f"ts={datetime.now(timezone.utc).isoformat()}",
                f"url={url}",
                "status=empty",
                "note=no bridge status has been reported yet",
            ]
        )

    events = payload.get("events")
    event_count = len(events) if isinstance(events, list) else 0
    latest_event = events[-1] if event_count else {}
    latest_event_stage = latest_event.get("stage") if isinstance(latest_event, dict) else None
    latest_event_message = latest_event.get("message") if isinstance(latest_event, dict) else None

    lines = [
        "QCLAW_IMAGE_BRIDGE_STATUS",
        f"ts={datetime.now(timezone.utc).isoformat()}",
        f"url={url}",
        f"mode={payload.get('mode', 'unknown')}",
        f"transport={payload.get('transport', 'unknown')}",
        f"stage={payload.get('stage', 'unknown')}",
        f"message={payload.get('message', '')}",
        f"prompt_length={payload.get('prompt_length', 0)}",
        f"size={payload.get('size', 'unknown')}",
        f"quality={payload.get('quality', 'unknown')}",
        f"output_format={payload.get('output_format', 'unknown')}",
        f"success={payload.get('success')}",
        f"error={payload.get('error')}",
        f"events={event_count}",
    ]
    if latest_event_stage is not None:
        lines.append(f"latest_event_stage={latest_event_stage}")
    if latest_event_message is not None:
        lines.append(f"latest_event_message={latest_event_message}")
    if payload.get("image_base64"):
        lines.append("image_ready=yes")
    else:
        lines.append("image_ready=no")
    return "\n".join(lines)


def emit_once(url: str, timeout: float, print_json: bool) -> int:
    try:
        payload = fetch_status(url, timeout)
    except HTTPError as exc:
        print(
            "\n".join(
                [
                    "QCLAW_IMAGE_BRIDGE_STATUS",
                    f"ts={datetime.now(timezone.utc).isoformat()}",
                    f"url={url}",
                    f"status=http_error",
                    f"http_status={exc.code}",
                    f"reason={exc.reason}",
                ]
            ),
            file=sys.stdout,
        )
        return 2
    except URLError as exc:
        print(
            "\n".join(
                [
                    "QCLAW_IMAGE_BRIDGE_STATUS",
                    f"ts={datetime.now(timezone.utc).isoformat()}",
                    f"url={url}",
                    "status=network_error",
                    f"reason={exc.reason}",
                ]
            ),
            file=sys.stdout,
        )
        return 3
    except Exception as exc:
        print(
            "\n".join(
                [
                    "QCLAW_IMAGE_BRIDGE_STATUS",
                    f"ts={datetime.now(timezone.utc).isoformat()}",
                    f"url={url}",
                    "status=parse_error",
                    f"reason={exc}",
                ]
            ),
            file=sys.stdout,
        )
        return 4

    print(summarize(payload, url))
    if print_json and payload is not None:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    resolved_url = resolve_url(args.url, args.base_url)

    if args.watch:
        try:
            while True:
                code = emit_once(resolved_url, args.timeout, args.json)
                if code != 0:
                    return code
                time.sleep(max(0.5, args.interval))
        except KeyboardInterrupt:
            print("\nQCLAW_IMAGE_BRIDGE_STATUS stopped by user")
            return 0

    return emit_once(resolved_url, args.timeout, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
