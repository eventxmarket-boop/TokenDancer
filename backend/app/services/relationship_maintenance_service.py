from __future__ import annotations

from typing import Any

from app.services.intimate_companion_service import detect_emotional_state, retrieve_relevant_memories


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _clean_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


def build_relationship_maintenance_context(persona: dict[str, Any], history: list[dict[str, str]], user_message: str) -> str:
    payload = persona.get("intimate_relationship_maintenance") or {}
    relationship_profile = payload.get("relationship_profile") or persona.get("relationship_profile") or {}
    memory_base = persona.get("intimate_memory_base") or {}
    emotional_state = detect_emotional_state(user_message, history)
    memories = retrieve_relevant_memories(memory_base if isinstance(memory_base, dict) else {}, emotional_state, user_message)
    interaction_patterns = _clean_lines(payload.get("interaction_patterns"))
    maintenance_goals = _clean_lines(payload.get("maintenance_goals"))
    conversation_samples = _clean_lines(payload.get("conversation_samples"))
    lines: list[str] = [
        "亲密关系路径：关系维护",
        f"当前情绪状态：{emotional_state}",
        f"当前用户消息：{_normalize_text(user_message)}",
    ]
    if isinstance(relationship_profile, dict):
        name = _normalize_text(relationship_profile.get("name"))
        stage = _normalize_text(relationship_profile.get("relationship_stage"))
        tone = _normalize_text(relationship_profile.get("tone"))
        response_temperature = _normalize_text(relationship_profile.get("response_temperature"))
        if name:
            lines.append(f"关系对象：{name}")
        if stage:
            lines.append(f"关系阶段：{stage}")
        if tone:
            lines.append(f"对方风格：{tone}")
        if response_temperature:
            lines.append(f"回复温度：{response_temperature}")
    if conversation_samples:
        lines.append("聊天样本：")
        lines.extend(f"- {item}" for item in conversation_samples[:4])
    if interaction_patterns:
        lines.append("互动模式：")
        lines.extend(f"- {item}" for item in interaction_patterns[:4])
    if maintenance_goals:
        lines.append("维护目标：")
        lines.extend(f"- {item}" for item in maintenance_goals[:4])
    if memories:
        lines.append("可调用记忆：")
        lines.extend(f"- {item}" for item in memories[:4])
    return "\n".join(lines).strip()
