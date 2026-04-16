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


def build_past_relationship_context(persona: dict[str, Any], history: list[dict[str, str]], user_message: str) -> str:
    payload = persona.get("intimate_past_relationship") or {}
    persona_profile = payload.get("persona_profile") or persona.get("relationship_profile") or {}
    memory_base = persona.get("intimate_memory_base") or {}
    emotional_state = detect_emotional_state(user_message, history)
    memories = retrieve_relevant_memories(memory_base if isinstance(memory_base, dict) else {}, emotional_state, user_message)
    relationship_memory = _clean_lines(payload.get("relationship_memory"))
    expression_samples = _clean_lines(payload.get("expression_samples"))
    boundaries = _clean_lines(payload.get("boundaries"))
    lines: list[str] = [
        "亲密关系路径：过去关系 / 自我镜像",
        f"当前情绪状态：{emotional_state}",
        f"当前用户消息：{_normalize_text(user_message)}",
    ]
    if isinstance(persona_profile, dict):
        name = _normalize_text(persona_profile.get("name"))
        relationship_type = _normalize_text(persona_profile.get("relationship_type"))
        remembrance_style = _normalize_text(persona_profile.get("remembrance_style"))
        tone = _normalize_text(persona_profile.get("tone"))
        response_temperature = _normalize_text(persona_profile.get("response_temperature"))
        if name:
            lines.append(f"对象称呼：{name}")
        if relationship_type:
            lines.append(f"角色类型：{relationship_type}")
        if remembrance_style:
            lines.append(f"回忆方式：{remembrance_style}")
        if tone:
            lines.append(f"说话风格：{tone}")
        if response_temperature:
            lines.append(f"回应温度：{response_temperature}")
    if relationship_memory:
        lines.append("关系记忆：")
        lines.extend(f"- {item}" for item in relationship_memory[:4])
    if expression_samples:
        lines.append("语气样本：")
        lines.extend(f"- {item}" for item in expression_samples[:4])
    if boundaries:
        lines.append("边界提醒：")
        lines.extend(f"- {item}" for item in boundaries[:4])
    if memories:
        lines.append("可调用记忆：")
        lines.extend(f"- {item}" for item in memories[:4])
    return "\n".join(lines).strip()
