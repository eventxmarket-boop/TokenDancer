from __future__ import annotations

import re
from typing import Any


SAD_HINTS = ("难过", "失落", "委屈", "伤心", "低落", "沮丧", "想哭", "崩溃", "心累")
ANXIOUS_HINTS = ("焦虑", "压力", "紧张", "担心", "害怕", "慌", "着急", "失眠", "考试", "工作压力")
HAPPY_HINTS = ("开心", "高兴", "好消息", "顺利", "进步", "录取", "上岸", "拿到", "通过", "喜悦")
ADVICE_HINTS = ("怎么办", "建议", "要不要", "该不该", "怎么做", "帮我看看", "值不值", "如何选择")

FAMILY_SUBTYPE_LABELS = {
    "mother": "妈妈",
    "parents": "父母",
    "other_family": "其他家人",
}

FAMILY_SUBTYPE_FOCUS = {
    "mother": "更偏接住情绪、细节照顾和熟悉安慰",
    "parents": "更偏家庭整体视角、稳定建议和共同记忆",
    "other_family": "更偏通用家庭陪伴和自然关心",
}


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _clean_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


def detect_emotional_state(user_message: str, history: list[dict[str, str]]) -> str:
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

    if any(hint in text for hint in SAD_HINTS):
        return "难过 / 失落"
    if any(hint in text for hint in ANXIOUS_HINTS):
        return "焦虑 / 压力"
    if any(hint in text for hint in HAPPY_HINTS):
        return "开心 / 分享喜悦"
    if any(hint in text for hint in ADVICE_HINTS):
        return "寻求建议"
    return "日常聊天"


def _memory_sources(memory_base: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for key in (
        "shared_events",
        "important_advice",
        "daily_habits",
        "emotional_triggers",
        "memory_fragments",
        "text_materials",
        "image_notes",
        "voice_notes",
    ):
        items.extend(_clean_lines(memory_base.get(key)))
    chat_history_summary = _normalize_text(memory_base.get("chat_history_summary"))
    if chat_history_summary:
        items.append(chat_history_summary)
    return [item for item in items if item]


def _emotion_rules_payload(persona: dict[str, Any]) -> dict[str, Any]:
    emotion_rules = persona.get("emotion_rules") or {}
    return emotion_rules if isinstance(emotion_rules, dict) else {}


def _family_subtype(value: Any) -> str:
    subtype = _normalize_text(value).lower()
    if subtype in {"mother", "mama", "mom", "妈妈", "母亲"}:
        return "mother"
    if subtype in {"parents", "parent", "father", "dad", "父母", "爸爸", "父亲"}:
        return "parents"
    if subtype in {"other_family", "other family", "其他家人"}:
        return "other_family"
    return "mother"


def retrieve_relevant_memories(
    memory_base: dict[str, Any],
    emotional_state: str,
    user_message: str,
) -> list[str]:
    candidates = _memory_sources(memory_base)
    if not candidates:
        return []

    message = _normalize_text(user_message)
    emotional_keywords = {
        "难过 / 失落": SAD_HINTS,
        "焦虑 / 压力": ANXIOUS_HINTS,
        "开心 / 分享喜悦": HAPPY_HINTS,
        "寻求建议": ADVICE_HINTS,
        "日常聊天": (),
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
        if len(item) <= 12:
            score += 1
        scored.append((score, index, item))

    scored.sort(key=lambda entry: (-entry[0], entry[1]))
    selected = [item for score, _, item in scored if score > 0][:4]
    if selected:
        return selected

    return candidates[:3]


def build_family_reply_context(
    persona_profile: dict[str, Any],
    emotional_state: str,
    memories: list[str],
    user_message: str,
    *,
    emotion_rules: dict[str, Any] | None = None,
    family_subtype: str = "",
) -> str:
    emotion_rules = emotion_rules if isinstance(emotion_rules, dict) else {}
    subtype = _family_subtype(family_subtype or persona_profile.get("family_subtype"))
    tone = _normalize_text(persona_profile.get("tone"))
    comfort_style = _normalize_text(persona_profile.get("comfort_style"))
    celebration_style = _normalize_text(persona_profile.get("celebration_style"))
    boundaries = _normalize_text(persona_profile.get("boundaries"))
    relationship_type = _normalize_text(persona_profile.get("relationship_type"))
    name = _normalize_text(persona_profile.get("name"))
    catchphrases = _clean_lines(persona_profile.get("catchphrases"))

    temperature_map = {
        "难过 / 失落": "温暖、稳定、先接情绪",
        "焦虑 / 压力": "安抚但不空泛，先帮对方稳住",
        "开心 / 分享喜悦": "跟着高兴，顺着把好消息说完整",
        "寻求建议": "先安抚，再给具体建议",
        "日常聊天": "自然、熟悉、轻松",
    }
    rule_temperature_map = emotion_rules.get("response_temperature_map")
    if isinstance(rule_temperature_map, dict):
        mapped_temperature = _normalize_text(rule_temperature_map.get(emotional_state))
        if mapped_temperature:
            temperature_map[emotional_state] = mapped_temperature
    temperature = temperature_map.get(emotional_state, "自然、熟悉、轻松")
    emotion_summary = _normalize_text(emotion_rules.get("summary"))
    response_sequence = _clean_lines(emotion_rules.get("response_sequence"))
    memory_priority_rules = _clean_lines(emotion_rules.get("memory_priority_rules"))
    boundary_rules = _clean_lines(emotion_rules.get("boundary_rules"))

    parts = [
        f"当前情绪状态：{emotional_state}",
        f"建议回应温度：{temperature}",
    ]
    subtype_label = FAMILY_SUBTYPE_LABELS.get(subtype, subtype or "妈妈")
    subtype_focus = FAMILY_SUBTYPE_FOCUS.get(subtype, FAMILY_SUBTYPE_FOCUS["mother"])
    parts.append(f"家人子类型：{subtype_label}（{subtype_focus}）")
    if relationship_type or name:
        parts.append(f"家人身份：{relationship_type or name}")
    if tone:
        parts.append(f"说话风格：{tone}")
    if comfort_style:
        parts.append(f"安慰方式：{comfort_style}")
    if celebration_style:
        parts.append(f"分享喜悦方式：{celebration_style}")
    if catchphrases:
        parts.append("常用口头禅：")
        parts.extend(f"- {item}" for item in catchphrases[:4])
    if memories:
        parts.append("可调用回忆：")
        parts.extend(f"- {item}" for item in memories[:4])
    chat_history_summary = _normalize_text(persona_profile.get("chat_history_summary"))
    if chat_history_summary:
        parts.append(f"聊天记录摘要：{chat_history_summary}")
    if boundaries:
        parts.append(f"边界提醒：{boundaries}")
    if emotion_summary:
        parts.append(f"情绪规则摘要：{emotion_summary}")
    if response_sequence:
        parts.append("回复顺序：")
        parts.extend(f"- {item}" for item in response_sequence[:4])
    if memory_priority_rules:
        parts.append("记忆优先级：")
        parts.extend(f"- {item}" for item in memory_priority_rules[:4])
    if boundary_rules:
        parts.append("规则边界：")
        parts.extend(f"- {item}" for item in boundary_rules[:4])
    parts.append(f"当前用户消息：{_normalize_text(user_message)}")
    return "\n".join(parts).strip()


def build_family_companion_context(
    persona: dict[str, Any],
    history: list[dict[str, str]],
    user_message: str,
) -> str:
    persona_profile = persona.get("persona_profile") or {}
    memory_base = persona.get("memory_base") or {}
    if not isinstance(persona_profile, dict) or not isinstance(memory_base, dict):
        return ""

    emotional_state = detect_emotional_state(user_message, history)
    memories = retrieve_relevant_memories(memory_base, emotional_state, user_message)
    emotion_rules = _emotion_rules_payload(persona)
    family_subtype = _normalize_text(persona.get("family_subtype") or persona_profile.get("family_subtype"))
    return build_family_reply_context(
        persona_profile,
        emotional_state,
        memories,
        user_message,
        emotion_rules=emotion_rules,
        family_subtype=family_subtype,
    )
