from __future__ import annotations

from typing import Any


PLATFORM_CONSTRAINT = (
    "你不是在表演角色，你要用该人格的判断方式、思考路径和表达倾向帮助用户解决问题。"
    "不要机械重复用户原话，不要只给口号，要给出具体判断、理由、代价和可执行建议。"
    "优先先给结论，再补充理由与下一步。"
    "回答时优先体现该人格的判断顺序，而不仅仅是模仿语气。"
    "先给出核心判断，再解释依据、代价、适用条件和下一步建议。"
    "对于教育规划、专业选择、考研、就业判断类问题，优先体现先问条件、再看出路、再算代价的判断顺序，不要只模仿语气。"
    "避免只说风格化短句，避免空泛口号。"
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
    return build_persona_system_prompt_with_context(persona)


def build_persona_system_prompt_with_context(
    persona: dict[str, Any],
    facts_context: str | None = None,
) -> str:
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
    if facts_context:
        _append_section(parts, "研究事实摘要", facts_context)
        parts.append(
            "研究后回答约束：当问题涉及具体院校、专业、录取线、保研率、就业率、薪资或政策变化时，"
            "先基于已获取的事实摘要判断，再给结论。不要跳过事实层直接拍脑袋回答。纯框架问题才允许直接基于判断模型回答。"
        )

    parts.append(f"平台统一约束：{PLATFORM_CONSTRAINT}")
    return "\n\n".join(parts).strip()


def build_chat_messages(
    persona: dict[str, Any],
    history: list[dict[str, str]],
    user_message: str,
    *,
    facts_context: str | None = None,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": build_persona_system_prompt_with_context(persona, facts_context=facts_context),
        },
    ]

    for message in history:
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message.strip()})
    return messages
