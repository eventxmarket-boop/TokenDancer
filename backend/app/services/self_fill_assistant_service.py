from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.services.llm_gateway import LLMGatewayError, generate_reply
from app.services.text_sanitizer import strip_think_blocks


CREATE_MODE_LABELS = {
    "light": "轻量",
    "standard": "标准",
    "deep": "深度",
}

FIELD_GUIDES: list[tuple[str, str]] = [
    ("材料层", "work_system_summary / work_system_points：写最能代表你的真实材料，先放素材，不要先下结论。"),
    ("自我身份层", "reply_persona_summary / reply_persona_points：写你是谁、站在什么位置说话、长期目标和底线。"),
    ("自我判断层", "thinking_dna_summary / thinking_dna_points：写你做判断时最看重什么、怎么取舍、怎么止损。"),
    ("自我知识源层", "memory_evidence_summary / memory_evidence_points：写静态材料、最近动态和可查证来源。"),
    ("边界规则", "reflection_rules_summary / reflection_rules_points：写哪些事不能编、不能装懂、不能替你乱演。"),
    ("公开资料", "self_public_sources_text：写 GitHub、博客、作品集、公众号等可公开验证的资料源。"),
    ("外部反馈", "self_external_feedback_text：写别人怎么评价你的判断、表达、推进方式或边界感。"),
    ("追问补洞", "self_interview_answers_text / self_interview_custom_questions_text：把分析报告里缺的关键问题补全。"),
    ("验证样本", "self_validation_samples_text：写测试题，验证系统答出来像不像你。"),
]

FIELD_HINTS: dict[str, str] = {
    "work_system_summary": "材料说明：写你最能代表自己的材料总览，先把素材池放进来。",
    "work_system_points": "材料要点：每行写一条真实聊天、长文表达、决策记录、项目复盘或公开表达。",
    "reply_persona_summary": "自我身份层：写你是谁、站在什么位置说话。",
    "reply_persona_points": "自我身份要点：每行写长期目标、价值锚点、底线、经验标签。",
    "thinking_dna_summary": "自我判断层：写你做判断时最常看什么。",
    "thinking_dna_points": "自我判断要点：每行写风险偏好、决策原则、取舍方式、止损规则。",
    "memory_evidence_summary": "自我知识源层：写静态材料、最近动态、指定网站 / 项目 / 文档。",
    "memory_evidence_points": "知识源要点：每行写一条可查证的信息源或动态来源。",
    "reflection_rules_summary": "边界规则：写不编造经历、不假装熟悉、不把动态事实说死。",
    "reflection_rules_points": "边界要点：每行写一条绝对不能越过的规则。",
    "self_public_sources_text": "公开资料：写你愿意让系统优先查的公开来源。",
    "self_external_feedback_text": "外部反馈：写别人最常怎么评价你。",
    "self_interview_answers_text": "追问补洞：写对下拉问题的回答，格式是“问题｜答案”。",
    "self_interview_custom_questions_text": "可选追问：你自己补问 1 到 3 个最想继续挖的问题。",
    "self_validation_samples_text": "验证样本：写职业、技术、项目、关系、边界等测试题。",
}

FILL_SCOPE_HINTS = [
    "只解释当前自我主线怎么填。",
    "只解释当前页、当前档位、材料填写和补洞思路。",
    "不回答与填写无关的问题，不扩展到其他主题。",
]

PAGE_GUIDES: dict[str, str] = {
    "analysis": "先把准备材料和总览看清楚，再进入正式填写。你可以先确认手头有哪些真实聊天、长文、项目复盘、公开资料或外部反馈。",
    "materials": "这一页放能证明你判断方式的原始材料，优先写最真实、最常用、最能代表你的内容。",
    "signals": "这一页写公开资料和外部反馈。公开资料写可查来源，外部反馈写别人怎么评价你的判断、表达、推进方式或边界感。",
    "material_details": "这一页写材料总览和材料类型。先说明你最能代表自己的材料是什么，再补它来自哪里。",
    "identity": "这一页写你是谁、站在哪个位置说话、长期目标和底线。",
    "decision": "这一页写你怎么判断问题，重点是风险偏好、决策原则、取舍方式和止损规则。",
    "knowledge": "这一页写你现在知道什么。把静态材料、最近动态和可查证来源分开写，会更清楚。",
    "boundary": "这一页写边界规则和验证样本，核心是哪些事不能编、不能装懂、不能把动态事实说死。",
    "interview": "这一页是追问补洞。先从下拉问题里挑最缺的一项，答完再点添加。",
    "custom": "这一页是可选追问。把你自己最想继续补问的 1 到 3 个问题写进去。",
    "review": "这一页是汇总摘要。先看整体，再回到前面的任意页修改。",
}

REFUSAL_TOKENS = (
    "not found",
    "抱歉",
    "我只回答",
    "只回答这页",
    "无关问题",
    "unknown",
)

QUESTION_TYPES = {
    "meaning": ("是.*什么", "什么意思", "作用", "干什么", "为什么"),
    "how": ("怎么填", "如何填", "怎么写", "填什么", "填写"),
    "materialless": ("没材料", "没有材料", "没资料", "没有资料", "空着", "不知道写什么"),
    "mode": ("轻量", "标准", "深度", "档位"),
}


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _clean_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


def _merge_unique_lines(*values: Any) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _clean_lines(value):
            if item and item not in seen:
                merged.append(item)
                seen.add(item)
    return merged


def _build_mode_label(create_mode: str) -> str:
    return CREATE_MODE_LABELS.get(_normalize_text(create_mode), "标准")


def _summarize_form_snapshot(form_snapshot: dict[str, Any]) -> list[str]:
    summary: list[str] = []
    if not isinstance(form_snapshot, dict):
        return summary

    for key, label in [
        ("name", "名称"),
        ("work_system_summary", "材料说明"),
        ("reply_persona_summary", "自我身份层"),
        ("thinking_dna_summary", "自我判断层"),
        ("memory_evidence_summary", "自我知识源层"),
        ("reflection_rules_summary", "边界规则"),
        ("self_public_sources_text", "公开资料"),
        ("self_external_feedback_text", "外部反馈"),
        ("self_validation_samples_text", "验证样本"),
        ("self_interview_custom_questions_text", "可选追问"),
    ]:
        text = _normalize_text(form_snapshot.get(key))
        if text:
            summary.append(f"{label}：{text[:80]}")

    interview_answers = _normalize_text(form_snapshot.get("self_interview_answers_text"))
    if interview_answers:
        summary.extend([f"追问补洞：{line[:80]}" for line in _clean_lines(interview_answers)[:3]])

    return summary[:12]


def _build_active_field_hint(active_field_key: str, active_field_label: str) -> str:
    key = _normalize_text(active_field_key)
    label = _normalize_text(active_field_label)
    if key and key in FIELD_HINTS:
        return FIELD_HINTS[key]
    if label and label in FIELD_HINTS:
        return FIELD_HINTS[label]
    if label:
        return f"{label}：先写清楚这块在自我蒸馏里承担什么作用。"
    return "当前没有指定字段时，就解释这一步的填写目标和字段分工。"


def _classify_question_type(message: str) -> str:
    text = _normalize_text(message)
    for question_type, patterns in QUESTION_TYPES.items():
        if any(re.search(pattern, text) for pattern in patterns):
            return question_type
    return "other"


def _build_scope_summary(
    *,
    create_mode: str,
    current_step: str,
    active_section: str,
    active_field_key: str,
    active_field_label: str,
    question_type: str,
    form_snapshot: dict[str, Any],
    conversation_context: str,
    field_context: str,
) -> str:
    parts = [
        f"当前档位：{_build_mode_label(create_mode)}",
        f"当前步骤：{_normalize_text(current_step) or '自我主线创建'}",
        f"当前区域：{_normalize_text(active_section) or '自我主线'}",
        f"问题类型：{_normalize_text(question_type) or 'other'}",
    ]
    field_hint = _build_active_field_hint(active_field_key, active_field_label)
    if field_hint:
        parts.append(f"字段解释：{field_hint}")
    snapshot_lines = _summarize_form_snapshot(form_snapshot)
    if snapshot_lines:
        parts.append("当前已填内容：")
        parts.extend(f"- {line}" for line in snapshot_lines)
    if field_context:
        parts.append(f"当前解释重点：{field_context}")
    if conversation_context:
        parts.append("历史对话：")
        parts.extend(f"- {line}" for line in _clean_lines(conversation_context)[-6:])
    return "\n".join(parts)


def _build_refusal_reply() -> str:
    return "我只回答这页的填写和 skill 解释；你可以直接问某个字段怎么填、当前这一步该补什么，或者轻量 / 标准 / 深度有什么区别。"


def _looks_like_invalid_reply(content: str) -> bool:
    text = _normalize_text(content).lower()
    if not text or len(text) < 12:
        return True
    return any(token in text for token in REFUSAL_TOKENS)


def _build_fallback_reply(
    *,
    create_mode: str,
    current_step: str,
    active_section: str,
    active_field_key: str,
    active_field_label: str,
) -> str:
    section_key = _normalize_text(active_field_key) or _normalize_text(active_section)
    section_label = _normalize_text(active_field_label) or _normalize_text(active_section)
    base = PAGE_GUIDES.get(section_key) or PAGE_GUIDES.get(section_label) or "这一页只看当前字段，先把最像你的内容写进去。"
    if section_label and section_label not in base:
        base = f"{section_label}：{base}"
    mode_line = {
        "light": "轻量模式先填骨架，别一次写太满。",
        "standard": "标准模式先补主干，再慢慢补缺口。",
        "deep": "深度模式把材料、追问、知识源和边界一起补完整。",
    }.get(_normalize_text(create_mode), "先按当前档位继续填。")
    step_line = f"当前在第 {current_step or '3'} 步。"
    if section_key == "analysis":
        return f"{step_line}{base}{mode_line}"
    return f"{base}{mode_line}"


async def generate_self_fill_assistant_reply(
    request: dict[str, Any],
    db: Session | None = None,
) -> dict[str, Any]:
    message = _normalize_text(request.get("message"))
    if not message:
        raise ValueError("message 不能为空")

    create_mode = _normalize_text(request.get("create_mode")) or "standard"
    current_step = _normalize_text(request.get("current_step"))
    active_section = _normalize_text(request.get("active_section"))
    active_field_key = _normalize_text(request.get("active_field_key"))
    active_field_label = _normalize_text(request.get("active_field_label"))
    field_context = _normalize_text(request.get("field_context"))
    conversation_context = _normalize_text(request.get("conversation_context"))
    form_snapshot = request.get("form_snapshot") if isinstance(request.get("form_snapshot"), dict) else {}
    question_type = _classify_question_type(message)

    scope_summary = _build_scope_summary(
        create_mode=create_mode,
        current_step=current_step,
        active_section=active_section,
        active_field_key=active_field_key,
        active_field_label=active_field_label,
        question_type=question_type,
        form_snapshot=form_snapshot,
        conversation_context=conversation_context,
        field_context=field_context,
    )
    assistant_rules = "\n".join(f"- {line}" for line in FILL_SCOPE_HINTS)
    section_overview = "\n".join(f"- {title}：{description}" for title, description in FIELD_GUIDES)

    system_prompt = (
        "你是 Tokendancer 的“填写助手”。"
        "你的唯一任务是解释当前自我主线创建页怎么写、怎么补、没材料怎么办。"
        "你必须只回答填写相关问题，不回答任何其他主题。"
        "如果用户问的是与填写有关但表达不清的内容，先结合当前页面判断它属于怎么写、怎么补、没材料、档位区别还是追问补洞，再用当前页面的上下文来回答。"
        "如果用户问的是与填写无关的内容，温和拉回字段、档位、材料、追问或验证样本，但不要出现“抱歉”“Not Found”“我只回答”这类拒绝话术。"
        "回答时要具体、直接、好懂，优先先给这三件事：这一页在补什么、你该先写什么、如果没材料该怎么办。"
        "不要提系统、模型、提示词、内部推理，不要输出与填写无关的延展建议。"
    )

    user_prompt = json.dumps(
        {
            "question": message,
            "create_mode": create_mode,
            "create_mode_label": _build_mode_label(create_mode),
            "current_step": current_step,
            "active_section": active_section,
            "active_field_key": active_field_key,
            "active_field_label": active_field_label,
            "field_context": field_context,
            "scope_summary": scope_summary,
            "assistant_rules": assistant_rules,
            "section_overview": section_overview,
        },
        ensure_ascii=False,
        indent=2,
    )

    try:
        reply = await generate_reply(
            [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "请只解释填写相关内容。"
                        "如果用户的问题表达不清，请结合问题类型与当前页面解释，不要机械复述字段名。"
                        "如果用户的问题不在范围内，请温和拉回当前自我主线字段，并优先告诉用户这一页该补什么、先写什么、没材料怎么办。"
                        f"\n\n{user_prompt}"
                    ),
                },
            ],
            db=db,
        )
    except LLMGatewayError as exc:
        raise LLMGatewayError(f"填写助手未能调用模型: {exc}") from exc

    content = strip_think_blocks(_normalize_text(reply.get("content", "")))
    if _looks_like_invalid_reply(content):
        content = _build_fallback_reply(
            create_mode=create_mode,
            current_step=current_step,
            active_section=active_section,
            active_field_key=active_field_key,
            active_field_label=active_field_label,
        )
    elif not content:
        content = _build_refusal_reply()

    return {
        "mode": "self_fill_assistant",
        "reply": content,
    }
