from __future__ import annotations

from typing import Any


PLATFORM_CONSTRAINT = (
    "你不是在表演角色，你要用该人格的判断方式、思考路径和表达倾向帮助用户解决问题。"
    "不要机械重复用户原话，不要只给口号，要给出具体判断、理由、代价和可执行建议。"
    "优先先给结论，再补充理由与下一步。"
    "当信息不足时，明确指出缺失条件。"
    "不要输出思考过程、推理草稿、内部分析。"
    "不要输出 <think>、<reasoning>、<analysis> 或类似标签。"
    "只输出给用户看的最终答案，不要复述内部判断过程。"
)


def _append_section(parts: list[str], title: str, content: str) -> None:
    text = (content or "").strip()
    if not text:
        return
    parts.append(f"## {title}\n{text}")


def build_persona_system_prompt(persona: dict[str, Any]) -> str:
    meta = persona.get("meta") or {}
    parts: list[str] = [
        "你正在为 Tokendancer persona 子站提供回复。"
        "请严格基于所给人格 skill 作答，不要输出模板化占位文案。",
        f"人格名称：{meta.get('name', '')}",
        f"人格标识：{meta.get('slug', '')}",
    ]

    _append_section(parts, "人格身份与定位", persona.get("profile", ""))
    _append_section(parts, "思维方式", persona.get("mindset", ""))
    _append_section(parts, "决策规则", persona.get("heuristics", ""))
    _append_section(parts, "表达风格", persona.get("expression", ""))
    _append_section(parts, "示例风格", persona.get("persona_examples", ""))
    _append_section(parts, "当前状态", persona.get("state", ""))
    _append_section(parts, "边界规则", persona.get("guardrails", ""))

    parts.append(f"平台统一约束：{PLATFORM_CONSTRAINT}")
    return "\n\n".join(parts).strip()


def build_chat_messages(
    persona: dict[str, Any],
    history: list[dict[str, str]],
    user_message: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": build_persona_system_prompt(persona)},
    ]

    for message in history:
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message.strip()})
    return messages
