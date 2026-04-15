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


def _append_layer_section(parts: list[str], title: str, layer: Any) -> None:
    if not layer:
        return

    summary = ""
    points: list[str] = []
    if isinstance(layer, dict):
        summary = str(layer.get("summary") or layer.get("title") or "").strip()
        raw_points = layer.get("points") or layer.get("items") or layer.get("details") or []
        if isinstance(raw_points, list):
            points = [str(item).strip() for item in raw_points if str(item).strip()]
        else:
            text_points = str(raw_points or "").strip()
            points = [line.strip("•- \t") for line in text_points.splitlines() if line.strip()]
    else:
        summary = str(getattr(layer, "summary", "") or "").strip()
        raw_points = getattr(layer, "points", []) or []
        if isinstance(raw_points, list):
            points = [str(item).strip() for item in raw_points if str(item).strip()]

    if not summary and not points:
        return

    lines: list[str] = []
    if summary:
        lines.append(summary)
    lines.extend(f"- {point}" for point in points)
    _append_section(parts, title, "\n".join(lines))


def build_persona_system_prompt(persona: dict[str, Any]) -> str:
    return build_persona_system_prompt_with_context(persona)


def build_persona_system_prompt_with_context(
    persona: dict[str, Any],
    session_summary: str | None = None,
    facts_context: str | None = None,
    aux_context: str | None = None,
) -> str:
    meta = persona.get("meta") or {}
    parts: list[str] = [
        "你正在为 Tokendancer persona 子站提供回复。"
        "请严格基于所给人格 skill 作答，不要输出模板化占位文案。",
        f"人格名称：{meta.get('name', '')}",
        f"人格标识：{meta.get('slug', '')}",
    ]

    self_unified = persona.get("self_persona_unified") or {}
    if self_unified:
        _append_layer_section(parts, "做事方式", self_unified.get("work_system"))
        _append_layer_section(parts, "回复方式", self_unified.get("reply_persona"))
        _append_layer_section(parts, "思考方式", self_unified.get("thinking_dna"))
        _append_layer_section(parts, "生活痕迹", self_unified.get("memory_evidence"))
        _append_layer_section(parts, "反思规则", self_unified.get("reflection_rules"))
        _append_section(parts, "边界规则", persona.get("guardrails", ""))
    reunion_persona = persona.get("reunion_persona_profile") or {}
    reunion_memory = persona.get("reunion_memory_base") or {}
    reunion_policy = persona.get("reunion_memory_retrieval_policy") or {}
    reunion_guardrails = persona.get("reunion_safety_guardrails") or {}
    if reunion_persona:
        profile_lines = []
        for label, key in [
            ("重逢身份", "relationship_type"),
            ("称呼", "name"),
            ("说话风格", "tone"),
            ("回忆方式", "remembrance_style"),
            ("安抚方式", "comfort_style"),
            ("边界", "boundaries"),
        ]:
            value = str(reunion_persona.get(key, "")).strip()
            if value:
                profile_lines.append(f"- {label}：{value}")
        _append_section(parts, "人格层", "\n".join(profile_lines))

        memory_lines = []
        for label, key in [
            ("聊天记录摘要", "chat_history_summary"),
            ("日记 / 信件", "diary_notes"),
            ("照片 / 截图", "photo_notes"),
            ("口述回忆", "voice_notes"),
            ("记忆片段", "memory_fragments"),
            ("共同记忆", "shared_memories"),
        ]:
            value = reunion_memory.get(key, []) if isinstance(reunion_memory, dict) else []
            if isinstance(value, list):
                text = " / ".join(str(item).strip() for item in value if str(item).strip())
            else:
                text = str(value or "").strip()
            if text:
                memory_lines.append(f"- {label}：{text}")
        _append_section(parts, "记忆层", "\n".join(memory_lines))

        policy_lines = []
        for label, key in [
            ("检索模式", "mode"),
            ("渐进式回忆", "progressive_recall"),
        ]:
            value = reunion_policy.get(key, "") if isinstance(reunion_policy, dict) else ""
            if isinstance(value, bool):
                text = "是" if value else "否"
            else:
                text = str(value or "").strip()
            if text:
                policy_lines.append(f"- {label}：{text}")
        for label, key in [("优先规则", "priority_rules"), ("降级规则", "fallback_rules")]:
            value = reunion_policy.get(key, []) if isinstance(reunion_policy, dict) else []
            if isinstance(value, list):
                text = " / ".join(str(item).strip() for item in value if str(item).strip())
            else:
                text = str(value or "").strip()
            if text:
                policy_lines.append(f"- {label}：{text}")
        _append_section(parts, "记忆检索策略", "\n".join(policy_lines))

        guardrail_lines = []
        for label, key in [
            ("边界", "boundaries"),
            ("情绪护栏", "emotional_protection"),
            ("避免触发", "avoid_triggers"),
        ]:
            value = reunion_guardrails.get(key, []) if isinstance(reunion_guardrails, dict) else []
            if isinstance(value, list):
                text = " / ".join(str(item).strip() for item in value if str(item).strip())
            else:
                text = str(value or "").strip()
            if text:
                guardrail_lines.append(f"- {label}：{text}")
        _append_section(parts, "安全护栏", "\n".join(guardrail_lines))
    else:
        _append_section(parts, "人格身份与定位", persona.get("profile", ""))
        _append_section(parts, "思维方式", persona.get("mindset", ""))
        _append_section(parts, "决策规则", persona.get("heuristics", ""))
        _append_section(parts, "表达风格", persona.get("expression", ""))
        _append_section(parts, "示例风格", persona.get("persona_examples", ""))
        _append_section(parts, "当前状态", persona.get("state", ""))
        _append_section(parts, "边界规则", persona.get("guardrails", ""))
    if session_summary:
        _append_section(parts, "会话摘要（仅供内部理解上下文）", session_summary)
    if facts_context:
        _append_section(parts, "研究事实摘要", facts_context)
        parts.append(
            "研究后回答约束：当问题涉及具体院校、专业、录取线、保研率、就业率、薪资或政策变化时，"
            "先基于已获取的事实摘要判断，再给结论。不要跳过事实层直接拍脑袋回答。纯框架问题才允许直接基于判断模型回答。"
        )
    if aux_context:
        _append_section(parts, "运行上下文（仅供内部理解）", aux_context)

    parts.append(f"平台统一约束：{PLATFORM_CONSTRAINT}")
    return "\n\n".join(parts).strip()


def build_chat_messages(
    persona: dict[str, Any],
    history: list[dict[str, str]],
    user_message: str,
    *,
    session_summary: str | None = None,
    facts_context: str | None = None,
    aux_context: str | None = None,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": build_persona_system_prompt_with_context(
                persona,
                session_summary=session_summary,
                facts_context=facts_context,
                aux_context=aux_context,
            ),
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
