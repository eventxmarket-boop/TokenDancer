from __future__ import annotations

import re
from typing import Any


GRIEF_HINTS = ("想念", "难过", "失落", "怀念", "告别", "离开", "难舍", "遗憾", "空落")
RECALL_HINTS = ("记得", "回忆", "以前", "那时候", "过去", "从前", "曾经", "重逢", "再见")
COMFORT_HINTS = ("怎么办", "难受", "想哭", "睡不着", "撑不住", "压力", "害怕")


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _clean_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


def detect_reunion_emotional_state(user_message: str, history: list[dict[str, str]]) -> str:
    text = " ".join(
        [
            _normalize_text(user_message),
            " ".join(
                _normalize_text(message.get("content"))
                for message in history[-4:]
                if _normalize_text(message.get("content"))
            ),
        ]
    )

    if any(hint in text for hint in GRIEF_HINTS):
        return "怀念 / 失落"
    if any(hint in text for hint in RECALL_HINTS):
        return "回忆 / 复盘"
    if any(hint in text for hint in COMFORT_HINTS):
        return "需要安抚"
    return "日常回顾"


def retrieve_relevant_memories(
    memory_base: dict[str, Any],
    emotional_state: str,
    user_message: str,
) -> list[str]:
    candidates: list[str] = []
    for key in (
        "chat_history_summary",
        "shared_memories",
        "memory_fragments",
        "diary_notes",
        "letter_notes",
        "photo_notes",
        "voice_notes",
    ):
        candidates.extend(_clean_lines(memory_base.get(key)))

    if not candidates:
        return []

    message = _normalize_text(user_message)
    emotional_keywords = {
        "怀念 / 失落": GRIEF_HINTS,
        "回忆 / 复盘": RECALL_HINTS,
        "需要安抚": COMFORT_HINTS,
        "日常回顾": (),
    }.get(emotional_state, ())

    scored: list[tuple[int, int, str]] = []
    for index, item in enumerate(candidates):
        score = 0
        if any(keyword in item for keyword in emotional_keywords):
            score += 3
        if any(keyword in item for keyword in message.split() if keyword):
            score += 2
        if emotional_state in item:
            score += 1
        if len(item) <= 20:
            score += 1
        scored.append((score, index, item))

    scored.sort(key=lambda entry: (-entry[0], entry[1]))
    selected = [item for score, _, item in scored if score > 0][:4]
    if selected:
        return selected
    return candidates[:3]


def build_reunion_reply_context(
    persona_profile: dict[str, Any],
    memory_base: dict[str, Any],
    retrieval_policy: dict[str, Any],
    safety_guardrails: dict[str, Any],
    emotional_state: str,
    memories: list[str],
    user_message: str,
) -> str:
    tone = _normalize_text(persona_profile.get("tone"))
    remembrance_style = _normalize_text(persona_profile.get("remembrance_style"))
    comfort_style = _normalize_text(persona_profile.get("comfort_style"))
    boundaries = _normalize_text(persona_profile.get("boundaries"))
    name = _normalize_text(persona_profile.get("name"))
    relationship_type = _normalize_text(persona_profile.get("relationship_type"))
    retrieval_mode = _normalize_text(retrieval_policy.get("mode"))
    progressive_recall = bool(retrieval_policy.get("progressive_recall", True))
    priority_rules = _clean_lines(retrieval_policy.get("priority_rules"))
    fallback_rules = _clean_lines(retrieval_policy.get("fallback_rules"))
    protection_notes = _clean_lines(safety_guardrails.get("emotional_protection"))
    avoid_triggers = _clean_lines(safety_guardrails.get("avoid_triggers"))
    history_summary = _normalize_text(memory_base.get("chat_history_summary"))

    temperature_map = {
        "怀念 / 失落": "克制、温柔、允许慢慢回忆",
        "回忆 / 复盘": "平稳、清楚、顺着往前讲",
        "需要安抚": "先稳住情绪，再慢慢说",
        "日常回顾": "轻一点、慢一点、保留记忆感",
    }
    temperature = temperature_map.get(emotional_state, "轻一点、慢一点、保留记忆感")

    parts = [
        f"当前情绪状态：{emotional_state}",
        f"建议回应温度：{temperature}",
    ]
    if relationship_type or name:
        parts.append(f"重逢身份：{relationship_type or name}")
    if tone:
        parts.append(f"说话风格：{tone}")
    if remembrance_style:
        parts.append(f"回忆方式：{remembrance_style}")
    if comfort_style:
        parts.append(f"安抚方式：{comfort_style}")
    if retrieval_mode:
        parts.append(f"记忆检索模式：{retrieval_mode}")
    parts.append(f"是否渐进式回忆：{'是' if progressive_recall else '否'}")
    if history_summary:
        parts.append(f"聊天记录摘要：{history_summary}")
    if priority_rules:
        parts.append("优先规则：")
        parts.extend(f"- {item}" for item in priority_rules[:4])
    if memories:
        parts.append("可调用回忆：")
        parts.extend(f"- {item}" for item in memories[:4])
    if fallback_rules:
        parts.append("降级规则：")
        parts.extend(f"- {item}" for item in fallback_rules[:3])
    if protection_notes:
        parts.append("心理护栏：")
        parts.extend(f"- {item}" for item in protection_notes[:3])
    if avoid_triggers:
        parts.append("应避免触发：")
        parts.extend(f"- {item}" for item in avoid_triggers[:3])
    if boundaries:
        parts.append(f"边界提醒：{boundaries}")
    parts.append(f"当前用户消息：{_normalize_text(user_message)}")
    return "\n".join(parts).strip()


def build_reunion_persona_context(
    persona: dict[str, Any],
    history: list[dict[str, str]],
    user_message: str,
) -> str:
    persona_profile = persona.get("reunion_persona_profile") or {}
    memory_base = persona.get("reunion_memory_base") or {}
    retrieval_policy = persona.get("reunion_memory_retrieval_policy") or {}
    safety_guardrails = persona.get("reunion_safety_guardrails") or {}
    if not isinstance(persona_profile, dict) or not isinstance(memory_base, dict):
        return ""

    emotional_state = detect_reunion_emotional_state(user_message, history)
    memories = retrieve_relevant_memories(memory_base, emotional_state, user_message)
    return build_reunion_reply_context(
        persona_profile,
        memory_base,
        retrieval_policy if isinstance(retrieval_policy, dict) else {},
        safety_guardrails if isinstance(safety_guardrails, dict) else {},
        emotional_state,
        memories,
        user_message,
    )
