from __future__ import annotations

import re
from typing import Any

from app.schemas.self_persona_unified import SelfPersonaUnifiedDraft, SelfPersonaUnifiedLayer


class SelfPersonaUnifiedError(RuntimeError):
    pass


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _split_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


def _extract_layer(form_data: dict[str, Any], layer_key: str, fallback_summary: str = "") -> SelfPersonaUnifiedLayer:
    raw_layer = form_data.get(layer_key)
    summary = ""
    points: list[str] = []

    if isinstance(raw_layer, dict):
        summary = _normalize_text(raw_layer.get("summary")) or _normalize_text(raw_layer.get("title"))
        points = _split_lines(raw_layer.get("points") or raw_layer.get("items") or raw_layer.get("details"))
    else:
        summary = _normalize_text(form_data.get(f"{layer_key}_summary"))
        points = _split_lines(
            form_data.get(f"{layer_key}_points")
            or form_data.get(f"{layer_key}_items")
            or form_data.get(f"{layer_key}_details")
        )

    if not summary and points:
        summary = points[0]
    if not summary:
        summary = fallback_summary
    return SelfPersonaUnifiedLayer(summary=summary, points=points)


def _layer_to_text(title: str, layer: SelfPersonaUnifiedLayer) -> str:
    pieces = [f"{title}：{layer.summary}".strip("：")]
    pieces.extend(f"- {point}" for point in layer.points if point)
    return "\n".join(piece for piece in pieces if piece).strip()


def build_self_persona_draft(form_data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(form_data, dict):
        raise SelfPersonaUnifiedError("form_data must be an object")

    create_mode = _normalize_text(form_data.get("create_mode")) or "standard"
    input_modes = form_data.get("input_modes")
    if isinstance(input_modes, list):
        normalized_input_modes = [_normalize_text(item) for item in input_modes if _normalize_text(item)]
    else:
        normalized_input_modes = _split_lines(input_modes)

    if not normalized_input_modes:
        fallback_mode = _normalize_text(form_data.get("input_mode")) or "manual_profile"
        normalized_input_modes = [fallback_mode]

    work_system = _extract_layer(
        form_data,
        "work_system",
        "围绕做事方式、节奏和优先级整理自我人格。",
    )
    reply_persona = _extract_layer(
        form_data,
        "reply_persona",
        "围绕表达方式、回应温度和边界感整理自我人格。",
    )
    thinking_dna = _extract_layer(
        form_data,
        "thinking_dna",
        "围绕判断顺序、取舍逻辑和思考习惯整理自我人格。",
    )
    memory_evidence = _extract_layer(
        form_data,
        "memory_evidence",
        "围绕聊天记录、文字片段和生活痕迹整理自我人格。",
    )
    reflection_rules = _extract_layer(
        form_data,
        "reflection_rules",
        "围绕盲点、边界和修正方式整理自我人格。",
    )

    profile = _layer_to_text("做事方式", work_system)
    mindset = _layer_to_text("思考方式", thinking_dna)
    heuristics = _layer_to_text("反思规则", reflection_rules)
    expression = _layer_to_text("回复方式", reply_persona)
    guardrails = _layer_to_text("生活痕迹", memory_evidence)

    return {
        "profile": profile,
        "mindset": mindset,
        "heuristics": heuristics,
        "expression": expression,
        "guardrails": guardrails,
        "name": _normalize_text(form_data.get("name")) or "我的人格",
        "create_mode": create_mode,
        "input_modes": normalized_input_modes,
        "self_persona_unified": SelfPersonaUnifiedDraft(
            create_mode=create_mode,
            input_modes=normalized_input_modes,
            work_system=work_system,
            reply_persona=reply_persona,
            thinking_dna=thinking_dna,
            memory_evidence=memory_evidence,
            reflection_rules=reflection_rules,
        ).model_dump(),
    }
