from __future__ import annotations

from typing import Any

from app.schemas.relationship_management import (
    RelationshipManagementMemoryBase,
    RelationshipManagementProfile,
)
from app.services.intimate_companion_service import detect_emotional_state


UNDERSTANDING_HINTS = (
    "理解",
    "分析",
    "意思",
    "意图",
    "雷区",
    "信号",
    "翻译",
    "训练",
    "沟通",
    "表达",
    "怎么看",
    "怎么想",
    "什么意思",
    "为什么",
)

MAINTENANCE_HINTS = (
    "维护",
    "经营",
    "修复",
    "长期",
    "稳定",
    "相处",
    "磨合",
    "安抚",
    "陪伴",
    "继续",
    "维持",
    "改善",
    "关系",
    "伴侣",
)


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _clean_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


def _merge_unique_lines(*values: Any) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _clean_lines(value):
            if item and item not in seen:
                merged.append(item)
                seen.add(item)
    return merged


def _collect_text_pool(*values: Any) -> str:
    return " ".join(part for part in (_normalize_text(value) for value in values) if part)


def infer_relationship_management_focus(*values: Any) -> dict[str, float | str]:
    text = _collect_text_pool(*values)
    if not text:
        return {
            "analysis_focus": "balanced",
            "understanding_weight": 0.5,
            "maintenance_weight": 0.5,
        }

    lower_text = text.lower()
    understanding_hits = sum(1 for hint in UNDERSTANDING_HINTS if hint in lower_text)
    maintenance_hits = sum(1 for hint in MAINTENANCE_HINTS if hint in lower_text)

    if understanding_hits == 0 and maintenance_hits == 0:
        return {
            "analysis_focus": "balanced",
            "understanding_weight": 0.5,
            "maintenance_weight": 0.5,
        }

    understanding_score = 0.5 + (understanding_hits * 0.12) + (1 if "关系理解" in text else 0) * 0.08
    maintenance_score = 0.5 + (maintenance_hits * 0.12) + (1 if "关系经营" in text or "关系维护" in text else 0) * 0.08
    total = understanding_score + maintenance_score
    understanding_weight = round(understanding_score / total, 2)
    maintenance_weight = round(maintenance_score / total, 2)

    if abs(understanding_weight - maintenance_weight) < 0.12:
        focus = "balanced"
    elif understanding_weight > maintenance_weight:
        focus = "understanding"
    else:
        focus = "maintenance"

    return {
        "analysis_focus": focus,
        "understanding_weight": understanding_weight,
        "maintenance_weight": maintenance_weight,
    }


def build_relationship_management_profile(
    *,
    relationship_type: str,
    name: str,
    relationship_stage: str,
    tone: str,
    response_temperature: str,
    catchphrases: list[str],
    boundaries: str,
    focus: dict[str, float | str],
) -> RelationshipManagementProfile:
    return RelationshipManagementProfile(
        relationship_type=_normalize_text(relationship_type),
        name=_normalize_text(name),
        relationship_stage=_normalize_text(relationship_stage),
        tone=_normalize_text(tone),
        response_temperature=_normalize_text(response_temperature),
        catchphrases=[item for item in catchphrases if _normalize_text(item)],
        boundaries=_normalize_text(boundaries),
        analysis_focus=_normalize_text(focus.get("analysis_focus")),
        understanding_weight=float(focus.get("understanding_weight") or 0.0),
        maintenance_weight=float(focus.get("maintenance_weight") or 0.0),
    )


def build_relationship_management_memory_base(
    *,
    relationship_memory: list[str],
    interaction_samples: list[str],
    style_samples: list[str],
    candidate_reply_cues: list[str],
    relationship_context: str,
    raw_materials: dict[str, Any],
    focus: dict[str, float | str],
) -> RelationshipManagementMemoryBase:
    return RelationshipManagementMemoryBase(
        relationship_memory=[item for item in relationship_memory if _normalize_text(item)],
        interaction_samples=[item for item in interaction_samples if _normalize_text(item)],
        style_samples=[item for item in style_samples if _normalize_text(item)],
        candidate_reply_cues=[item for item in candidate_reply_cues if _normalize_text(item)],
        relationship_context=_normalize_text(relationship_context),
        analysis_focus=_normalize_text(focus.get("analysis_focus")),
        understanding_weight=float(focus.get("understanding_weight") or 0.0),
        maintenance_weight=float(focus.get("maintenance_weight") or 0.0),
        raw_materials=raw_materials or {},
    )


def _memory_pool(memory_base: dict[str, Any]) -> dict[str, list[str]]:
    if not isinstance(memory_base, dict):
        return {"relationship_memory": [], "interaction_samples": [], "style_samples": [], "candidate_reply_cues": []}

    return {
        "relationship_memory": _merge_unique_lines(
            memory_base.get("relationship_memory"),
            memory_base.get("key_memories"),
            memory_base.get("conversation_samples"),
            memory_base.get("shared_memories"),
        ),
        "interaction_samples": _merge_unique_lines(
            memory_base.get("interaction_samples"),
            memory_base.get("interaction_rules"),
            memory_base.get("conversation_samples"),
            memory_base.get("misunderstanding_points"),
            memory_base.get("rewrite_targets"),
        ),
        "style_samples": _merge_unique_lines(
            memory_base.get("style_samples"),
            memory_base.get("reply_style_samples"),
            memory_base.get("expression_samples"),
            memory_base.get("maintenance_goals"),
        ),
        "candidate_reply_cues": _merge_unique_lines(
            memory_base.get("candidate_reply_cues"),
            memory_base.get("rewrite_targets"),
            memory_base.get("maintenance_goals"),
        ),
    }


def select_relationship_management_memory_layers(
    memory_base: dict[str, Any],
    emotional_state: str,
    user_message: str,
    *,
    history: list[dict[str, str]] | None = None,
) -> dict[str, list[str] | str]:
    pool = _memory_pool(memory_base)
    recent_history = [
        _normalize_text(message.get("content"))
        for message in (history or [])[-4:]
        if _normalize_text(message.get("content"))
    ]
    trigger_text = _collect_text_pool(emotional_state, user_message, " ".join(recent_history))
    trigger_lower = trigger_text.lower()
    stage = "balanced"
    if any(keyword in trigger_lower for keyword in ("难过", "失落", "焦虑", "压力", "委屈", "崩溃", "心累")):
        stage = "light"
    elif any(keyword in trigger_lower for keyword in ("理解", "什么意思", "为什么", "怎么想", "雷区", "信号", "分析")):
        stage = "medium"
    elif any(keyword in trigger_lower for keyword in ("长期", "维持", "经营", "修复", "磨合", "伴侣", "相处")):
        stage = "deep"

    if stage == "light":
        selected = pool["style_samples"][:2] or pool["candidate_reply_cues"][:2] or pool["relationship_memory"][:1]
    elif stage == "medium":
        selected = (
            pool["interaction_samples"][:2]
            + pool["style_samples"][:1]
            + pool["relationship_memory"][:1]
        )
    else:
        selected = (
            pool["relationship_memory"][:2]
            + pool["interaction_samples"][:1]
            + pool["style_samples"][:1]
        )

    selected = [item for item in selected if item]
    if not selected:
        selected = pool["relationship_memory"][:2] or pool["interaction_samples"][:2] or pool["style_samples"][:2]

    max_memory_items = {"light": 2, "medium": 3, "deep": 4}.get(stage, 3)

    return {
        "recall_stage": stage,
        "max_memory_items": max_memory_items,
        "selected_memories": selected[:max_memory_items],
        "relationship_memory": pool["relationship_memory"],
        "interaction_samples": pool["interaction_samples"],
        "style_samples": pool["style_samples"],
        "candidate_reply_cues": pool["candidate_reply_cues"],
    }


def build_relationship_management_context(
    persona: dict[str, Any],
    history: list[dict[str, str]],
    user_message: str,
) -> str:
    profile = persona.get("relationship_management_profile") or persona.get("relationship_profile") or {}
    memory_base = (
        persona.get("relationship_management_memory_base")
        or persona.get("intimate_memory_base")
        or persona.get("memory_base")
        or {}
    )
    if not isinstance(profile, dict) or not isinstance(memory_base, dict):
        return ""

    emotional_state = detect_emotional_state(user_message, history)
    focus = infer_relationship_management_focus(
        profile.get("relationship_type"),
        profile.get("relationship_stage"),
        profile.get("tone"),
        profile.get("response_temperature"),
        user_message,
        " ".join(message.get("content", "") for message in history[-4:]),
        memory_base.get("relationship_context"),
        memory_base.get("relationship_memory"),
        memory_base.get("interaction_samples"),
        memory_base.get("style_samples"),
        memory_base.get("candidate_reply_cues"),
    )
    selected = select_relationship_management_memory_layers(memory_base, emotional_state, user_message, history=history)
    lines: list[str] = [
        "亲密关系路径：关系经营",
        f"分析重心：{focus['analysis_focus']}",
        f"理解权重：{focus['understanding_weight']}",
        f"维护权重：{focus['maintenance_weight']}",
        f"当前情绪状态：{emotional_state}",
        f"当前用户消息：{_normalize_text(user_message)}",
    ]
    relationship_type = _normalize_text(profile.get("relationship_type"))
    relationship_stage = _normalize_text(profile.get("relationship_stage"))
    tone = _normalize_text(profile.get("tone"))
    response_temperature = _normalize_text(profile.get("response_temperature"))
    catchphrases = _clean_lines(profile.get("catchphrases"))
    boundaries = _normalize_text(profile.get("boundaries"))
    if relationship_type:
        lines.append(f"关系类型：{relationship_type}")
    if relationship_stage:
        lines.append(f"关系阶段：{relationship_stage}")
    if tone:
        lines.append(f"说话风格：{tone}")
    if response_temperature:
        lines.append(f"回复温度：{response_temperature}")
    if catchphrases:
        lines.append("口头禅：")
        lines.extend(f"- {item}" for item in catchphrases[:4])
    if selected.get("selected_memories"):
        lines.append("当前召回：")
        lines.extend(f"- {item}" for item in selected["selected_memories"][:4])
    if boundaries:
        lines.append(f"边界提醒：{boundaries}")
    return "\n".join(lines).strip()

