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


def build_intimate_understanding_context(persona: dict[str, Any], history: list[dict[str, str]], user_message: str) -> str:
    payload = persona.get("intimate_understanding") or {}
    relationship_context = payload.get("relationship_context") or persona.get("relationship_profile") or {}
    memory_base = persona.get("intimate_memory_base") or {}
    emotional_state = detect_emotional_state(user_message, history)
    memories = retrieve_relevant_memories(memory_base if isinstance(memory_base, dict) else {}, emotional_state, user_message)
    conversation_samples = _clean_lines(payload.get("conversation_samples"))
    misunderstanding_points = _clean_lines(payload.get("misunderstanding_points"))
    rewrite_targets = _clean_lines(payload.get("rewrite_targets"))
    lines: list[str] = [
        "亲密关系路径：关系理解",
        f"当前情绪状态：{emotional_state}",
        f"关系上下文：{_normalize_text(relationship_context.get('relationship_type') if isinstance(relationship_context, dict) else '')}",
        f"关系阶段：{_normalize_text(relationship_context.get('relationship_stage') if isinstance(relationship_context, dict) else '')}",
        f"当前用户消息：{_normalize_text(user_message)}",
    ]
    if isinstance(relationship_context, dict):
        focus = _normalize_text(relationship_context.get("focus"))
        tone = _normalize_text(relationship_context.get("speech_style"))
        boundaries = _normalize_text(relationship_context.get("boundaries"))
        if focus:
            lines.append(f"理解目标：{focus}")
        if tone:
            lines.append(f"对方风格：{tone}")
        if boundaries:
            lines.append(f"边界提醒：{boundaries}")
    if conversation_samples:
        lines.append("聊天样本：")
        lines.extend(f"- {item}" for item in conversation_samples[:4])
    if misunderstanding_points:
        lines.append("误解点：")
        lines.extend(f"- {item}" for item in misunderstanding_points[:4])
    if rewrite_targets:
        lines.append("改写目标：")
        lines.extend(f"- {item}" for item in rewrite_targets[:4])
    if memories:
        lines.append("可调用记忆：")
        lines.extend(f"- {item}" for item in memories[:4])
    return "\n".join(lines).strip()
