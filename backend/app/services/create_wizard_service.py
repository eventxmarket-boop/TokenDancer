from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.schemas.create_wizard import CreateWizardDraftMeta
from app.schemas.family_companion import FamilyCompanionMemoryBase, FamilyCompanionPersonaProfile
from app.schemas.intimate_companion import (
    IntimateCompanionMemoryBase,
    IntimateCompanionRelationshipProfile,
)
from app.schemas.reunion_persona import (
    ReunionPersonaMemoryBase,
    ReunionPersonaProfile,
    ReunionPersonaRetrievalPolicy,
    ReunionPersonaSafetyGuardrails,
)
from app.services.self_persona_unified_service import build_self_persona_draft


class CreateWizardError(RuntimeError):
    pass


SUPPORTED_CREATE_TYPES = {
    "self_unified",
    "source_persona",
    "relationship_persona",
    "family_companion",
    "reunion_persona",
    "intimate_companion",
}

SELF_UNIFIED_SOURCE_REPO = "self-skill+nuwa-skill+forge-skill+digital-life"
FAMILY_COMPANION_SOURCE_REPO = "parents-skills+MamaSkill"
LEGACY_FAMILY_COMPANION_SOURCE_REPO = "MamaSkill+parents-skills+darwin-skill"
REUNION_PERSONA_SOURCE_REPO = "reunion-skill"
INTIMATE_UNDERSTANDING_SOURCE_REPO = "relationship-training-skill+xinyi"
INTIMATE_SIMULATION_SOURCE_REPO = "crush-skill"
INTIMATE_PARTNER_SOURCE_REPO = "partner-skill+npy-skill"
INTIMATE_PAST_RELATION_SOURCE_REPO = "ex-skill+first-love-skill+shuixian-skill"

CREATE_TYPE_LABELS = {
    "self_unified": "我的人格",
    "source_persona": "从资料创建人格",
    "relationship_persona": "关系人格",
    "family_companion": "家人陪伴",
    "reunion_persona": "重逢人格",
    "intimate_companion": "亲密关系",
}

CREATE_TYPE_CONFIG = {
    "self_unified": {
        "group": "self",
        "source_repo": SELF_UNIFIED_SOURCE_REPO,
        "repo_url": "https://github.com/moyitech/self-skill",
        "source_repos": ["self-skill", "nuwa-skill", "forge-skill", "digital-life"],
        "source_hint": "自我人格融合模板",
    },
    "source_persona": {
        "group": "source",
        "source_repo": "anyone-to-skill",
        "repo_url": "https://github.com/OpenDemon/anyone-to-skill",
        "source_repos": ["anyone-to-skill"],
        "source_hint": "资料蒸馏器",
    },
    "relationship_persona": {
        "group": "relationship",
        "source_repo": "relationship-skill-kit",
        "repo_url": "https://github.com/titanwings/colleague-skill",
        "source_repos": ["colleague-skill", "supervisor", "senpai-skill", "professor-skill", "Professor_skill"],
        "source_hint": "关系人格模板",
    },
    "family_companion": {
        "group": "relationship_family",
        "source_repo": FAMILY_COMPANION_SOURCE_REPO,
        "repo_url": "https://github.com/jiangziyan-693/MamaSkill",
        "source_repos": ["parents-skills", "MamaSkill"],
        "source_hint": "家人陪伴模板",
    },
    "reunion_persona": {
        "group": "relationship_family",
        "source_repo": REUNION_PERSONA_SOURCE_REPO,
        "repo_url": "https://github.com/yangdongchen66-boop/reunion-skill",
        "source_repos": ["reunion-skill"],
        "source_hint": "重逢人格模板",
    },
    "intimate_companion": {
        "group": "relationship_intimate",
        "source_repo": INTIMATE_UNDERSTANDING_SOURCE_REPO,
        "repo_url": "https://github.com/kroxchan/xinyi",
        "source_repos": [
            INTIMATE_UNDERSTANDING_SOURCE_REPO,
            INTIMATE_SIMULATION_SOURCE_REPO,
            INTIMATE_PARTNER_SOURCE_REPO,
            INTIMATE_PAST_RELATION_SOURCE_REPO,
        ],
        "source_hint": "亲密关系模板",
    },
}

INPUT_MODE_BY_SOURCE_REPO = {
    "self-skill": "manual_profile",
    "nuwa-skill": "documents",
    "forge-skill": "chat_history",
    "digital-life": "documents",
    SELF_UNIFIED_SOURCE_REPO: "manual_profile",
    "anyone-to-skill": "documents",
    "colleague-skill": "colleague",
    "boss-skills": "boss",
    "supervisor": "supervisor",
    "senpai-skill": "senpai",
    "professor-skill": "professor_a",
    "Professor_skill": "professor_b",
    "ex-skill": "ex",
    "relationship-training-skill": "relationship_training",
    "npy-skill": "ideal_partner",
    "crush-skill": "crush",
    "partner-skill": "partner",
    "first-love-skill": "first_love",
    "shuixian-skill": "self_mirror",
    "xinyi": "relationship_interpreter",
    "parents-skills": "parents",
    FAMILY_COMPANION_SOURCE_REPO: "mother",
    LEGACY_FAMILY_COMPANION_SOURCE_REPO: "mother",
    "reunion-skill": "reunion",
    "MamaSkill": "mama",
    REUNION_PERSONA_SOURCE_REPO: "chat_history",
    "digital-twin-skill": "multi_source",
    "immortal-skill": "multi_source",
    "anti-distill": "documents",
    "relationship-training-skill": "relationship_understanding",
    "xinyi": "relationship_understanding",
    INTIMATE_UNDERSTANDING_SOURCE_REPO: "relationship_understanding",
    "crush-skill": "message_simulation",
    "partner-skill": "partner_maintenance",
    "npy-skill": "partner_maintenance",
    INTIMATE_SIMULATION_SOURCE_REPO: "message_simulation",
    INTIMATE_PARTNER_SOURCE_REPO: "partner_maintenance",
    "ex-skill": "past_relation_mirror",
    "first-love-skill": "past_relation_mirror",
    "shuixian-skill": "past_relation_mirror",
    INTIMATE_PAST_RELATION_SOURCE_REPO: "past_relation_mirror",
}

SCHEMA_KEY_BY_SOURCE_REPO = {
    "self-skill": "self_persona",
    "nuwa-skill": "self_mindset_distill",
    "forge-skill": "self_deep_self_persona",
    "digital-life": "self_digital_trace_persona",
    SELF_UNIFIED_SOURCE_REPO: "self_unified",
    "anyone-to-skill": "source_anyone_from_sources",
    "colleague-skill": "relationship_workplace_colleague",
    "boss-skills": "relationship_workplace_boss",
    "supervisor": "relationship_academia_supervisor",
    "senpai-skill": "relationship_academia_senpai",
    "professor-skill": "relationship_academia_professor_a",
    "Professor_skill": "relationship_academia_professor_b",
    "relationship-training-skill": "intimate_companion_relationship_understanding",
    "xinyi": "intimate_companion_relationship_understanding",
    INTIMATE_UNDERSTANDING_SOURCE_REPO: "intimate_companion_relationship_understanding",
    "crush-skill": "intimate_companion_message_simulation",
    "partner-skill": "intimate_companion_partner_maintenance",
    "npy-skill": "intimate_companion_partner_maintenance",
    INTIMATE_SIMULATION_SOURCE_REPO: "intimate_companion_message_simulation",
    INTIMATE_PARTNER_SOURCE_REPO: "intimate_companion_partner_maintenance",
    "ex-skill": "intimate_companion_past_relation_mirror",
    "first-love-skill": "intimate_companion_past_relation_mirror",
    "shuixian-skill": "intimate_companion_past_relation_mirror",
    INTIMATE_PAST_RELATION_SOURCE_REPO: "intimate_companion_past_relation_mirror",
    "parents-skills": "relationship_family_parents",
    FAMILY_COMPANION_SOURCE_REPO: "family_companion_mother",
    LEGACY_FAMILY_COMPANION_SOURCE_REPO: "family_companion_mother",
    "reunion-skill": "relationship_family_reunion",
    "MamaSkill": "relationship_family_mama",
    REUNION_PERSONA_SOURCE_REPO: "reunion_persona_chat_history",
    "digital-twin-skill": "digital_twin_high_fidelity",
    "immortal-skill": "digital_twin_immortal",
    "anti-distill": "protection_anti_distill",
}

REPO_URL_BY_SOURCE_REPO = {
    "self-skill": "https://github.com/moyitech/self-skill",
    "nuwa-skill": "https://github.com/alchaincyf/nuwa-skill",
    "forge-skill": "https://github.com/YIKUAIBANZI/forge-skill",
    "digital-life": "https://github.com/wildbyteai/digital-life",
    SELF_UNIFIED_SOURCE_REPO: "https://github.com/moyitech/self-skill",
    "anyone-to-skill": "https://github.com/OpenDemon/anyone-to-skill",
    "colleague-skill": "https://github.com/titanwings/colleague-skill",
    "boss-skills": "https://github.com/vogtsw/boss-skills",
    "supervisor": "https://github.com/ybq22/supervisor",
    "senpai-skill": "https://github.com/zhanghaichao520/senpai-skill",
    "professor-skill": "https://github.com/CommitHu502Craft/professor-skill",
    "Professor_skill": "https://github.com/Azurboy/Professor_skill",
    "ex-skill": "https://github.com/titanwings/ex-skill",
    "relationship-training-skill": "https://github.com/TammyTan516/relationship-training-skill",
    "npy-skill": "https://github.com/wwwttlll/npy-skill",
    "crush-skill": "https://github.com/yyyyyyylll/crush-skill",
    "partner-skill": "https://github.com/NatalieCao323/partner-skill",
    "first-love-skill": "https://github.com/z969081067-commits/first-love-skill",
    "shuixian-skill": "https://github.com/Cyh29hao/shuixian-skill",
    "xinyi": "https://github.com/kroxchan/xinyi",
    INTIMATE_UNDERSTANDING_SOURCE_REPO: "https://github.com/kroxchan/xinyi",
    INTIMATE_SIMULATION_SOURCE_REPO: "https://github.com/yyyyyyylll/crush-skill",
    INTIMATE_PARTNER_SOURCE_REPO: "https://github.com/NatalieCao323/partner-skill",
    INTIMATE_PAST_RELATION_SOURCE_REPO: "https://github.com/titanwings/ex-skill",
    "parents-skills": "https://github.com/xiaoheizi8/parents-skills",
    "reunion-skill": "https://github.com/yangdongchen66-boop/reunion-skill",
    "MamaSkill": "https://github.com/jiangziyan-693/MamaSkill",
    FAMILY_COMPANION_SOURCE_REPO: "https://github.com/jiangziyan-693/MamaSkill",
    LEGACY_FAMILY_COMPANION_SOURCE_REPO: "https://github.com/jiangziyan-693/MamaSkill",
    REUNION_PERSONA_SOURCE_REPO: "https://github.com/yangdongchen66-boop/reunion-skill",
    "digital-twin-skill": "https://github.com/FredHJC/digital-twin-skill",
    "immortal-skill": "https://github.com/agenmod/immortal-skill",
    "anti-distill": "https://github.com/leilei926524-tech/anti-distill",
}

RELATIONSHIP_LABELS = {
    "colleague": "同事",
    "boss": "老板",
    "supervisor": "导师",
    "senpai": "师兄",
    "professor_a": "大学老师",
    "professor_b": "大学老师",
    "ex": "前任",
    "relationship_training": "关系训练",
    "ideal_partner": "理想伴侣",
    "crush": "暧昧对象",
    "partner": "现任伴侣",
    "first_love": "初恋",
    "self_mirror": "自我镜像伴侣",
    "relationship_interpreter": "关系理解辅助",
    "relationship_understanding": "关系理解",
    "message_simulation": "消息模拟",
    "partner_maintenance": "关系维护",
    "past_relation_mirror": "过去关系 / 自我镜像",
    "parents": "父母",
    "mother": "妈妈",
    "other_family": "其他家人",
    "reunion": "重逢人格",
    "mama": "妈妈",
}

INPUT_MODE_LABELS = {
    "self_persona": {
        "manual_profile": "手动填写",
        "chat_history": "聊天记录",
        "documents": "文档资料",
    },
    "source_persona": {
        "documents": "PDF / 文档",
        "chat_history": "聊天记录",
        "audio_video": "音频 / 视频",
        "multi_source": "多源资料",
    },
    "relationship_persona": {
        "colleague": "同事",
        "boss": "老板",
        "supervisor": "导师",
        "senpai": "师兄",
        "professor_a": "大学老师",
        "professor_b": "大学老师（模板 B）",
    },
    "intimate_companion": {
        "relationship_understanding": "关系理解",
        "message_simulation": "消息模拟",
        "partner_maintenance": "关系维护",
        "past_relation_mirror": "过去关系 / 自我镜像",
    },
    "family_companion": {
        "mother": "妈妈",
        "parents": "父母",
        "other_family": "其他家人",
    },
    "reunion_persona": {
        "chat_history": "聊天记录",
        "documents": "日记 / 信件",
        "memory_notes": "回忆片段",
        "photo_notes": "照片 / 截图说明",
        "voice_notes": "口述回忆",
    },
}


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


SELF_UNIFIED_ALIASES = {
    "self_persona",
    "self_mindset_distill",
    "self_deep_self_persona",
    "self_digital_trace_persona",
}


def _normalize_slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "draft"


def _clean_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


def _format_bullets(items: list[str]) -> str:
    if not items:
        return "- 暂无"
    return "\n".join(f"- {item}" for item in items)


def _validate_create_type(create_type: str) -> str:
    normalized = _normalize_text(create_type)
    if normalized in SELF_UNIFIED_ALIASES:
        normalized = "self_unified"
    if normalized not in SUPPORTED_CREATE_TYPES:
        raise CreateWizardError(f"Unsupported create_type: {create_type}")
    return normalized


def _resolve_input_mode(create_type: str, source_repo: str, schema_key: str) -> str:
    if schema_key and schema_key in INPUT_MODE_LABELS.get(create_type, {}):
        return schema_key
    if source_repo and source_repo in INPUT_MODE_BY_SOURCE_REPO:
        return INPUT_MODE_BY_SOURCE_REPO[source_repo]
    if create_type == "self_unified":
        return "manual_profile"
    if create_type == "source_persona":
        return "documents"
    if create_type == "family_companion":
        return "mother"
    if create_type == "reunion_persona":
        return "chat_history"
    if create_type == "intimate_companion":
        return "relationship_understanding"
    return "colleague"


def _resolve_schema_key(create_type: str, source_repo: str, input_mode: str, display_name: str) -> str:
    if create_type == "self_unified":
        return "self_unified"
    if create_type == "family_companion":
        return f"family_companion_{input_mode or 'mother'}"
    if create_type == "reunion_persona":
        return f"reunion_persona_{input_mode or 'chat_history'}"
    if create_type == "intimate_companion":
        return f"intimate_companion_{input_mode or 'relationship_understanding'}"
    if source_repo and source_repo in SCHEMA_KEY_BY_SOURCE_REPO:
        return SCHEMA_KEY_BY_SOURCE_REPO[source_repo]
    fallback = f"{create_type}_{input_mode or 'default'}"
    return f"{fallback}_{_normalize_slug(display_name)}" if display_name else fallback


def _build_self_draft(form_data: dict[str, Any], display_name: str = "") -> dict[str, Any]:
    unified_form: dict[str, Any] = {
        "name": _normalize_text(form_data.get("name")) or _normalize_text(display_name) or "我的人格",
        "create_mode": _normalize_text(form_data.get("create_mode")) or "standard",
        "input_modes": form_data.get("input_modes") or [form_data.get("input_mode") or "manual_profile"],
    }

    for layer_key, fallback in [
        ("work_system", "先把重要的事做好，再让表达尽量清楚。"),
        ("reply_persona", "回答时先说结论，再说理由。"),
        ("thinking_dna", "先梳理目标，再判断路径是否可行。"),
        ("memory_evidence", "把重要经历、聊天片段和生活痕迹整理进来。"),
        ("reflection_rules", "保留边界，不越过不愿意暴露的部分。"),
    ]:
        raw_summary = _normalize_text(form_data.get(f"{layer_key}_summary"))
        raw_points = _clean_lines(
            form_data.get(f"{layer_key}_points")
            or form_data.get(f"{layer_key}_details")
            or form_data.get(f"{layer_key}_items")
            or form_data.get(layer_key)
        )
        unified_form[layer_key] = {
            "summary": raw_summary or fallback,
            "points": raw_points,
        }

    return build_self_persona_draft(unified_form)


def _build_source_draft(form_data: dict[str, Any], display_name: str = "") -> dict[str, str]:
    name = _normalize_text(form_data.get("target_name")) or _normalize_text(display_name) or "资料人格"
    material_type = _normalize_text(form_data.get("material_type")) or "文档资料"
    material_description = _normalize_text(form_data.get("material_description")) or "从现有资料中提炼一个更像的回应方式。"
    focus_points = _clean_lines(form_data.get("focus_points")) or [
        "保留最关键的判断路径",
        "提炼有代表性的表达习惯",
    ]
    excluded_content = _clean_lines(form_data.get("excluded_content")) or [
        "不抽取隐私敏感信息",
        "不保留明显跑题内容",
    ]

    profile = (
        f"目标人格：{name}\n"
        f"材料类型：{material_type}\n"
        f"材料说明：{material_description}"
    )
    mindset = _format_bullets(
        [
            "先判断材料是否足够代表这个人格",
            "先保留可用于回答问题的稳定模式",
            "如果材料碎片化，先补足关键上下文再提炼",
        ]
    )
    heuristics = _format_bullets(
        [f"优先提炼：{point}" for point in focus_points] + ["先筛掉不适合进入人格的噪声材料"]
    )
    expression = _format_bullets(
        [
            "把材料里稳定出现的说法整理成可用表达风格",
            "输出时优先保留原有判断节奏，不做夸张改写",
            "回答要像被资料喂养出来，而不是只像一个壳子",
        ]
    )
    guardrails = _format_bullets(
        [f"不抽取：{item}" for item in excluded_content] + ["避免把边界内容误纳入人格草稿"]
    )
    return {
        "profile": profile,
        "mindset": mindset,
        "heuristics": heuristics,
        "expression": expression,
        "guardrails": guardrails,
        "name": name,
    }


def _build_relationship_draft(
    form_data: dict[str, Any],
    display_name: str = "",
    input_mode: str = "",
) -> dict[str, str]:
    relation_type = (
        _normalize_text(form_data.get("relationship_type"))
        or RELATIONSHIP_LABELS.get(_normalize_text(input_mode), "")
        or _normalize_text(display_name)
        or "关系人格"
    )
    name = _normalize_text(form_data.get("persona_name")) or _normalize_text(display_name) or relation_type
    speech_style = _normalize_text(form_data.get("speech_style")) or "表达比较直接。"
    decision_logic = _normalize_text(form_data.get("decision_logic")) or "先看现实条件，再看可行性。"
    purpose = _normalize_text(form_data.get("purpose")) or "帮助理解这段关系里的表达和判断。"
    boundaries = _normalize_text(form_data.get("boundaries")) or "不越过对方隐私和现实边界。"

    profile = (
        f"关系类型：{relation_type}\n"
        f"对象名称：{name}\n"
        f"用途：{purpose}"
    )
    mindset = _format_bullets(
        [
            f"先看对方常见的判断逻辑：{decision_logic}",
            "先保留关系语境，不把单句当成全貌",
            "条件不足时先追问关系背景",
        ]
    )
    heuristics = _format_bullets(
        [
            "先看对方会不会在意现实成本",
            "优先提炼关系中的稳定模式，而不是偶发情绪",
            "如果说话方式和目的不一致，优先相信反复出现的行为",
        ]
    )
    expression = _format_bullets(
        [
            f"说话风格：{speech_style}",
            "表达要贴近关系场景，不要过度抽象",
            "可以直接给建议，但要讲清楚代价",
        ]
    )
    guardrails = _format_bullets(
        [
            f"边界要求：{boundaries}",
            "不越界模拟真实身份之外的内容",
            "不把关系推断包装成确定事实",
        ]
    )
    return {
        "profile": profile,
        "mindset": mindset,
        "heuristics": heuristics,
        "expression": expression,
        "guardrails": guardrails,
        "name": name,
    }


def _build_family_companion_draft(
    form_data: dict[str, Any],
    display_name: str = "",
    input_mode: str = "",
) -> dict[str, Any]:
    relation_type = (
        _normalize_text(form_data.get("relationship_type"))
        or RELATIONSHIP_LABELS.get(_normalize_text(input_mode), "")
        or _normalize_text(display_name)
        or "家人陪伴"
    )
    name = _normalize_text(form_data.get("persona_name")) or _normalize_text(display_name) or relation_type
    tone = _normalize_text(form_data.get("speech_style")) or "温和、亲近、稳一点。"
    catchphrases = _clean_lines(form_data.get("catchphrases")) or ["先把情绪放一放", "别着急，慢慢来"]
    comfort_style = _normalize_text(form_data.get("comfort_style")) or "先接住情绪，再给安慰和陪伴。"
    celebration_style = _normalize_text(form_data.get("celebration_style")) or "先替你高兴，再顺着把好消息说完整。"
    boundaries = _normalize_text(form_data.get("relation_boundaries")) or "不碰隐私边界，不越界替你做决定。"
    shared_events = _clean_lines(form_data.get("shared_events")) or ["小时候一起吃饭的场景", "你难过时被安慰的瞬间"]
    important_advice = _clean_lines(form_data.get("important_advice")) or ["先照顾好自己", "遇到事先稳住再做决定"]
    daily_habits = _clean_lines(form_data.get("daily_habits")) or ["会关心你吃饭没", "会提醒你注意休息"]
    emotional_triggers = _clean_lines(form_data.get("emotional_triggers"))
    chat_history_summary = _normalize_text(form_data.get("chat_history_summary"))
    memory_fragments = _clean_lines(form_data.get("memory_fragments"))
    text_materials = _clean_lines(form_data.get("text_materials"))
    image_notes = _clean_lines(form_data.get("image_notes"))
    voice_notes = _clean_lines(form_data.get("voice_notes"))

    persona_profile = FamilyCompanionPersonaProfile(
        relationship_type=relation_type,
        name=name,
        tone=tone,
        catchphrases=catchphrases,
        comfort_style=comfort_style,
        celebration_style=celebration_style,
        boundaries=boundaries,
    )
    memory_base = FamilyCompanionMemoryBase(
        shared_events=shared_events,
        important_advice=important_advice,
        daily_habits=daily_habits,
        emotional_triggers=emotional_triggers,
        chat_history_summary=chat_history_summary,
        memory_fragments=memory_fragments,
        text_materials=text_materials,
        image_notes=image_notes,
        voice_notes=voice_notes,
    )

    profile = (
        f"家人陪伴定位：{relation_type}\n"
        f"称呼：{name}\n"
        f"说话风格：{tone}\n"
        f"主要用途：在你需要陪伴、安慰或分享好消息时，给出更贴近家人的回应。"
    )
    mindset = _format_bullets(
        [
            "先看对方的情绪状态，再决定是安慰、鼓励还是提醒",
            "先调动记忆里的熟悉感，再结合当前语境回应",
            "如果信息不足，先补充你们之间的关系背景",
        ]
    )
    heuristics = _format_bullets(
        [
            "难过时先接住情绪，再给稳一点的建议",
            "有好消息时先表达高兴，再顺着把喜悦说完整",
            "遇到边界话题时先收住，不越界逼问",
        ]
    )
    expression = _format_bullets(
        [
            f"常见说话感觉：{tone}",
            f"口头禅：{'；'.join(catchphrases)}",
            "回答时保持熟悉、自然、带温度",
        ]
    )
    guardrails = _format_bullets(
        [
            f"边界要求：{boundaries}",
            "不伪造不确定的家庭事实",
            "不把关心变成控制",
        ]
    )
    return {
        "profile": profile,
        "mindset": mindset,
        "heuristics": heuristics,
        "expression": expression,
        "guardrails": guardrails,
        "relationship_type": relation_type,
        "persona_profile": persona_profile.model_dump(),
        "memory_base": memory_base.model_dump(),
        "name": name,
    }


def _build_reunion_persona_draft(
    form_data: dict[str, Any],
    display_name: str = "",
    input_mode: str = "",
) -> dict[str, Any]:
    relation_type = (
        _normalize_text(form_data.get("relationship_type"))
        or RELATIONSHIP_LABELS.get(_normalize_text(input_mode), "")
        or _normalize_text(display_name)
        or "重逢人格"
    )
    name = _normalize_text(form_data.get("persona_name")) or _normalize_text(display_name) or relation_type
    tone = _normalize_text(form_data.get("tone")) or "克制、温柔、保留记忆感。"
    remembrance_style = _normalize_text(form_data.get("remembrance_style")) or "先慢慢回忆，再一点点靠近。"
    comfort_style = _normalize_text(form_data.get("comfort_style")) or "先稳住情绪，再带着记忆慢慢说。"
    boundaries = _normalize_text(form_data.get("boundaries")) or "不激进刺激，不越界替代现实。"
    chat_history_summary = _normalize_text(form_data.get("chat_history_summary"))
    diary_notes = _clean_lines(form_data.get("diary_notes"))
    letter_notes = _clean_lines(form_data.get("letter_notes"))
    photo_notes = _clean_lines(form_data.get("photo_notes"))
    voice_notes = _clean_lines(form_data.get("voice_notes"))
    memory_fragments = _clean_lines(form_data.get("memory_fragments"))
    shared_memories = _clean_lines(form_data.get("shared_memories"))
    retrieval_mode = _normalize_text(form_data.get("retrieval_mode")) or "渐进式回忆"
    priority_rules = _clean_lines(form_data.get("priority_rules")) or [
        "优先从最近的对话和回忆片段开始",
        "优先提取和当前情绪有关的记忆",
    ]
    fallback_rules = _clean_lines(form_data.get("fallback_rules")) or [
        "当记忆不足时，先稳住当前情绪",
        "不编造没有记录的具体细节",
    ]
    safety_boundaries = _clean_lines(form_data.get("safety_boundaries")) or [
        "不激进刺激情绪",
        "不替现实关系下结论",
    ]
    emotional_protection = _clean_lines(form_data.get("emotional_protection")) or [
        "先接住情绪，再慢慢回忆",
        "避免反复追问高压细节",
    ]
    avoid_triggers = _clean_lines(form_data.get("avoid_triggers")) or [
        "不要把空白补成确定事实",
        "不要一次性抛出过多强刺激回忆",
    ]

    persona_profile = ReunionPersonaProfile(
        relationship_type=relation_type,
        name=name,
        tone=tone,
        remembrance_style=remembrance_style,
        comfort_style=comfort_style,
        boundaries=boundaries,
    )
    memory_base = ReunionPersonaMemoryBase(
        chat_history_summary=chat_history_summary,
        diary_notes=diary_notes,
        letter_notes=letter_notes,
        photo_notes=photo_notes,
        voice_notes=voice_notes,
        memory_fragments=memory_fragments,
        shared_memories=shared_memories,
    )
    memory_retrieval_policy = ReunionPersonaRetrievalPolicy(
        mode=retrieval_mode,
        progressive_recall=True,
        priority_rules=priority_rules,
        fallback_rules=fallback_rules,
    )
    safety_guardrails = ReunionPersonaSafetyGuardrails(
        boundaries=safety_boundaries,
        emotional_protection=emotional_protection,
        avoid_triggers=avoid_triggers,
    )

    profile = (
        f"重逢人格定位：{relation_type}\n"
        f"称呼：{name}\n"
        f"说话风格：{tone}\n"
        f"回忆方式：{remembrance_style}\n"
        f"用途：从回忆和纪念材料里，慢慢整理出更克制、更温和的陪伴回应。"
    )
    mindset = _format_bullets(
        [
            "先判断当前情绪，再决定是回忆、安抚还是停顿",
            "先从少量相关记忆开始，不一下子铺满全部细节",
            "信息不足时先补上下文和材料来源",
        ]
    )
    heuristics = _format_bullets(
        [
            "优先采用渐进式回忆，不急着一次说完",
            "优先挑选与当前语境和情绪有关的片段",
            "当记忆和现实边界冲突时，先保护当下情绪",
        ]
    )
    expression = _format_bullets(
        [
            f"常见说话感觉：{tone}",
            f"回忆节奏：{remembrance_style}",
            "回答要克制、带记忆感，但不过度刺激情绪",
        ]
    )
    guardrails = _format_bullets(
        [
            f"边界要求：{boundaries}",
            "不激进刺激，不伪造未确认细节",
            "不把怀念变成对现实关系的替代",
        ]
    )
    return {
        "profile": profile,
        "mindset": mindset,
        "heuristics": heuristics,
        "expression": expression,
        "guardrails": guardrails,
        "relationship_type": relation_type,
        "reunion_persona_profile": persona_profile.model_dump(),
        "reunion_memory_base": memory_base.model_dump(),
        "reunion_memory_retrieval_policy": memory_retrieval_policy.model_dump(),
        "reunion_safety_guardrails": safety_guardrails.model_dump(),
        "name": name,
    }


def _build_intimate_companion_draft(
    form_data: dict[str, Any],
    display_name: str = "",
    input_mode: str = "",
) -> dict[str, Any]:
    relation_type = (
        _normalize_text(form_data.get("relationship_type"))
        or RELATIONSHIP_LABELS.get(_normalize_text(input_mode), "")
        or _normalize_text(display_name)
        or "亲密关系"
    )
    name = _normalize_text(form_data.get("persona_name")) or _normalize_text(display_name) or relation_type
    relationship_stage = _normalize_text(form_data.get("relationship_stage")) or "暧昧 / 关系中 / 磨合中"
    tone = _normalize_text(form_data.get("speech_style")) or "自然、亲近、带一点熟悉感。"
    response_temperature = _normalize_text(form_data.get("response_temperature")) or "先接住情绪，再顺着回应。"
    catchphrases = _clean_lines(form_data.get("catchphrases")) or ["最近怎么样", "我在听"]
    boundaries = _normalize_text(form_data.get("relation_boundaries")) or "不越界，不替对方下结论。"
    conversation_samples = _clean_lines(form_data.get("conversation_samples")) or [
        "你今天过得怎么样？",
        "最近在忙什么？",
    ]
    interaction_rules = _clean_lines(form_data.get("interaction_rules")) or [
        "先回应情绪，再给建议",
        "不要一下子逼问对方",
    ]
    relationship_goals = _clean_lines(form_data.get("relationship_goals")) or [
        "让沟通更顺畅",
        "让关系更稳定",
    ]
    key_memories = _clean_lines(form_data.get("key_memories")) or [
        "常聊的话题",
        "一起经历过的重要时刻",
    ]

    relationship_profile = IntimateCompanionRelationshipProfile(
        relationship_type=relation_type,
        name=name,
        relationship_stage=relationship_stage,
        tone=tone,
        response_temperature=response_temperature,
        catchphrases=catchphrases,
        boundaries=boundaries,
    )
    memory_base = IntimateCompanionMemoryBase(
        conversation_samples=conversation_samples,
        interaction_rules=interaction_rules,
        relationship_goals=relationship_goals,
        key_memories=key_memories,
    )

    profile = (
        f"亲密关系定位：{relation_type}\n"
        f"称呼：{name}\n"
        f"关系阶段：{relationship_stage}\n"
        f"说话风格：{tone}\n"
        f"回复温度：{response_temperature}"
    )
    mindset = _format_bullets(
        [
            "先看关系阶段，再决定是安抚、回应还是给建议",
            "先判断对方这句话想传达什么，再选择回应节奏",
            "信息不足时先补关系背景和对话样本",
        ]
    )
    heuristics = _format_bullets(
        [
            "先回应情绪，再进入内容本身",
            "优先用真实聊天样本里的节奏，而不是空泛模板",
            "如果当前问题涉及关系边界，先稳住边界再谈互动",
        ]
    )
    expression = _format_bullets(
        [
            f"常见说话感觉：{tone}",
            f"回应温度：{response_temperature}",
            f"口头禅：{'；'.join(catchphrases)}",
        ]
    )
    guardrails = _format_bullets(
        [
            f"边界要求：{boundaries}",
            "不伪造未确认的关系事实",
            "不把单条消息误判成全部关系状态",
        ]
    )
    return {
        "profile": profile,
        "mindset": mindset,
        "heuristics": heuristics,
        "expression": expression,
        "guardrails": guardrails,
        "relationship_type": relation_type,
        "relationship_profile": relationship_profile.model_dump(),
        "intimate_memory_base": memory_base.model_dump(),
        "name": name,
    }


def build_persona_draft(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_create_type = _validate_create_type(payload.get("create_type", ""))
    config = CREATE_TYPE_CONFIG[normalized_create_type]

    normalized_group = _normalize_text(payload.get("group")) or config["group"]
    normalized_source_repo = _normalize_text(payload.get("source_repo")) or config["source_repo"]
    normalized_display_name = _normalize_text(payload.get("display_name")) or _normalize_text(payload.get("name"))
    normalized_create_mode = _normalize_text(payload.get("create_mode")) or "standard"
    input_modes_payload = payload.get("input_modes")
    normalized_input_modes = (
        [str(item).strip() for item in input_modes_payload if str(item).strip()]
        if isinstance(input_modes_payload, list)
        else []
    )
    normalized_input_mode = _normalize_text(payload.get("input_mode")) or _resolve_input_mode(
        normalized_create_type,
        normalized_source_repo,
        _normalize_text(payload.get("schema_key")),
    )
    normalized_schema_key = _normalize_text(payload.get("schema_key")) or _resolve_schema_key(
        normalized_create_type,
        normalized_source_repo,
        normalized_input_mode,
        normalized_display_name,
    )
    form_data = payload.get("form_data") or {}
    if not isinstance(form_data, dict):
        raise CreateWizardError("form_data must be an object")

    if normalized_create_type == "self_unified":
        content = _build_self_draft(form_data, normalized_display_name)
    elif normalized_create_type == "source_persona":
        content = _build_source_draft(form_data, normalized_display_name)
    elif normalized_create_type == "family_companion":
        content = _build_family_companion_draft(form_data, normalized_display_name, normalized_input_mode)
    elif normalized_create_type == "reunion_persona":
        content = _build_reunion_persona_draft(form_data, normalized_display_name, normalized_input_mode)
    elif normalized_create_type == "intimate_companion":
        content = _build_intimate_companion_draft(form_data, normalized_display_name, normalized_input_mode)
    else:
        content = _build_relationship_draft(form_data, normalized_display_name, normalized_input_mode)

    content_name = content.pop("name")
    form_title = content_name or normalized_display_name or CREATE_TYPE_LABELS[normalized_create_type]
    generated_at = datetime.now(timezone.utc).isoformat()

    meta = CreateWizardDraftMeta(
        id=f"draft-{uuid4().hex[:8]}",
        slug=_normalize_slug(f"{normalized_create_type}-{form_title}"),
        name=form_title,
        category=normalized_group,
        display_name=normalized_display_name,
        version="V0.1.0-draft",
        status="draft",
        create_type=normalized_create_type,
        create_mode=normalized_create_mode,
        input_mode=normalized_input_mode,
        input_modes=normalized_input_modes or ([normalized_input_mode] if normalized_input_mode else []),
        group=normalized_group,
        schema_key=normalized_schema_key,
        source_repo=normalized_source_repo,
        repo_url=REPO_URL_BY_SOURCE_REPO.get(normalized_source_repo, config["repo_url"]),
        source_repos=list(config["source_repos"]) if normalized_create_type == "self_unified" else ([normalized_source_repo] if normalized_source_repo else list(config["source_repos"])),
        source_hint=config["source_hint"],
        generated_at=generated_at,
    )

    return {
        "meta": meta.model_dump(),
        "profile": content["profile"],
        "mindset": content["mindset"],
        "heuristics": content["heuristics"],
        "expression": content["expression"],
        "guardrails": content["guardrails"],
        "relationship_type": content.get("relationship_type", ""),
        "self_persona_unified": content.get("self_persona_unified"),
        "persona_profile": content.get("persona_profile"),
        "memory_base": content.get("memory_base"),
        "reunion_persona_profile": content.get("reunion_persona_profile"),
        "reunion_memory_base": content.get("reunion_memory_base"),
        "reunion_memory_retrieval_policy": content.get("reunion_memory_retrieval_policy"),
        "reunion_safety_guardrails": content.get("reunion_safety_guardrails"),
        "relationship_profile": content.get("relationship_profile"),
        "intimate_memory_base": content.get("intimate_memory_base"),
    }
