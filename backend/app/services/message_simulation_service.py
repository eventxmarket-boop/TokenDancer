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


def build_message_simulation_context(persona: dict[str, Any], history: list[dict[str, str]], user_message: str) -> str:
    payload = persona.get("intimate_message_simulation") or {}
    target_persona_profile = payload.get("target_persona_profile") or persona.get("relationship_profile") or {}
    conversation_context = payload.get("conversation_context") or {}
    memory_base = persona.get("intimate_memory_base") or {}
    emotional_state = detect_emotional_state(user_message, history)
    memories = retrieve_relevant_memories(memory_base if isinstance(memory_base, dict) else {}, emotional_state, user_message)
    reply_style_samples = _clean_lines(payload.get("reply_style_samples"))
    preferences = payload.get("simulation_preferences") or {}
    lines: list[str] = [
        "亲密关系路径：消息模拟",
        f"当前情绪状态：{emotional_state}",
        f"当前准备发送的话：{_normalize_text(user_message)}",
    ]
    if isinstance(target_persona_profile, dict):
        name = _normalize_text(target_persona_profile.get("name"))
        stage = _normalize_text(target_persona_profile.get("stage"))
        tone = _normalize_text(target_persona_profile.get("speech_style"))
        if name:
            lines.append(f"对方称呼：{name}")
        if stage:
            lines.append(f"关系阶段：{stage}")
        if tone:
            lines.append(f"对方风格：{tone}")
    if isinstance(conversation_context, dict):
        recent_context = _normalize_text(conversation_context.get("recent_context"))
        current_message = _normalize_text(conversation_context.get("current_message"))
        if recent_context:
            lines.append(f"最近上下文：{recent_context}")
        if current_message:
            lines.append(f"拟发消息：{current_message}")
    if reply_style_samples:
        lines.append("回复样本：")
        lines.extend(f"- {item}" for item in reply_style_samples[:4])
    if isinstance(preferences, dict):
        tone = _normalize_text(preferences.get("tone"))
        candidate_count = _normalize_text(preferences.get("candidate_count"))
        if tone:
            lines.append(f"语气偏好：{tone}")
        if candidate_count:
            lines.append(f"候选数量：{candidate_count}")
    if memories:
        lines.append("可调用记忆：")
        lines.extend(f"- {item}" for item in memories[:4])
    return "\n".join(lines).strip()
