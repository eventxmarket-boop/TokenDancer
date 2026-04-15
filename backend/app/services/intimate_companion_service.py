from __future__ import annotations

import re
from typing import Any


SAD_HINTS = ("难过", "失落", "委屈", "伤心", "低落", "沮丧", "想哭", "崩溃", "心累")
ANXIOUS_HINTS = ("焦虑", "压力", "紧张", "担心", "害怕", "慌", "着急", "失眠", "吃醋", "冷战")
HAPPY_HINTS = ("开心", "高兴", "好消息", "顺利", "进步", "在一起", "复合", "甜", "喜欢")
ADVICE_HINTS = ("怎么办", "建议", "要不要", "该不该", "怎么做", "帮我看看", "值不值", "如何选择")


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
    for key in ("conversation_samples", "interaction_rules", "relationship_goals", "key_memories"):
        items.extend(_clean_lines(memory_base.get(key)))
    return [item for item in items if item]


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
        if len(item) <= 16:
            score += 1
        scored.append((score, index, item))

    scored.sort(key=lambda entry: (-entry[0], entry[1]))
    selected = [item for score, _, item in scored if score > 0][:4]
    if selected:
        return selected

    return candidates[:3]


def build_intimate_reply_context(
    relationship_profile: dict[str, Any],
    emotional_state: str,
    memories: list[str],
    user_message: str,
) -> str:
    tone = _normalize_text(relationship_profile.get("tone"))
    response_temperature = _normalize_text(relationship_profile.get("response_temperature"))
    relationship_stage = _normalize_text(relationship_profile.get("relationship_stage"))
    boundaries = _normalize_text(relationship_profile.get("boundaries"))
    relationship_type = _normalize_text(relationship_profile.get("relationship_type"))
    name = _normalize_text(relationship_profile.get("name"))
    catchphrases = _clean_lines(relationship_profile.get("catchphrases"))

    temperature_map = {
        "难过 / 失落": "更温柔、更耐心，先接住情绪",
        "焦虑 / 压力": "先安抚，再帮忙梳理下一步",
        "开心 / 分享喜悦": "跟着高兴，顺着把开心说完整",
        "寻求建议": "先看关系状态，再给具体建议",
        "日常聊天": "自然、轻松、像熟悉的人聊天",
    }
    temperature = response_temperature or temperature_map.get(emotional_state, "自然、轻松、像熟悉的人聊天")

    parts = [
        f"当前情绪状态：{emotional_state}",
        f"建议回应温度：{temperature}",
    ]
    if relationship_type or name:
        parts.append(f"关系身份：{relationship_type or name}")
    if relationship_stage:
        parts.append(f"关系阶段：{relationship_stage}")
    if tone:
        parts.append(f"说话风格：{tone}")
    if catchphrases:
        parts.append("常用口头禅：")
        parts.extend(f"- {item}" for item in catchphrases[:4])
    if memories:
        parts.append("可调用回忆：")
        parts.extend(f"- {item}" for item in memories[:4])
    if boundaries:
        parts.append(f"边界提醒：{boundaries}")
    parts.append(f"当前用户消息：{_normalize_text(user_message)}")
    return "\n".join(parts).strip()


def build_intimate_companion_context(
    persona: dict[str, Any],
    history: list[dict[str, str]],
    user_message: str,
) -> str:
    relationship_profile = persona.get("relationship_profile") or persona.get("persona_profile") or {}
    memory_base = persona.get("intimate_memory_base") or persona.get("memory_base") or {}
    if not isinstance(relationship_profile, dict) or not isinstance(memory_base, dict):
        return ""

    emotional_state = detect_emotional_state(user_message, history)
    memories = retrieve_relevant_memories(memory_base, emotional_state, user_message)
    return build_intimate_reply_context(relationship_profile, emotional_state, memories, user_message)
