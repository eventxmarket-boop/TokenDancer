from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.schemas.create_wizard import CreateWizardDraftMeta


class CreateWizardError(RuntimeError):
    pass


SUPPORTED_CREATE_TYPES = {"self_persona", "source_persona", "relationship_persona"}

CREATE_TYPE_LABELS = {
    "self_persona": "自我人格",
    "source_persona": "从资料创建人格",
    "relationship_persona": "关系人格",
}

CREATE_TYPE_CONFIG = {
    "self_persona": {
        "group": "self",
        "source_repo": "self-skill",
        "repo_url": "https://github.com/moyitech/self-skill",
        "source_repos": ["self-skill", "nuwa-skill"],
        "source_hint": "自我人格模板",
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
        "source_repos": [
            "colleague-skill",
            "supervisor",
            "parents-skills",
            "partner-skill",
        ],
        "source_hint": "关系人格模板",
    },
}

INPUT_MODE_BY_SOURCE_REPO = {
    "self-skill": "manual_profile",
    "nuwa-skill": "documents",
    "forge-skill": "chat_history",
    "digital-life": "documents",
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
    "reunion-skill": "reunion",
    "MamaSkill": "mama",
    "digital-twin-skill": "multi_source",
    "immortal-skill": "multi_source",
    "anti-distill": "documents",
}

SCHEMA_KEY_BY_SOURCE_REPO = {
    "self-skill": "self_persona",
    "nuwa-skill": "self_mindset_distill",
    "forge-skill": "self_deep_self_persona",
    "digital-life": "self_digital_trace_persona",
    "anyone-to-skill": "source_anyone_from_sources",
    "colleague-skill": "relationship_workplace_colleague",
    "boss-skills": "relationship_workplace_boss",
    "supervisor": "relationship_academia_supervisor",
    "senpai-skill": "relationship_academia_senpai",
    "professor-skill": "relationship_academia_professor_a",
    "Professor_skill": "relationship_academia_professor_b",
    "ex-skill": "relationship_intimate_ex",
    "relationship-training-skill": "relationship_intimate_relationship_training",
    "npy-skill": "relationship_intimate_ideal_partner",
    "crush-skill": "relationship_intimate_crush",
    "partner-skill": "relationship_intimate_partner",
    "first-love-skill": "relationship_intimate_first_love",
    "shuixian-skill": "relationship_intimate_self_mirror",
    "xinyi": "relationship_intimate_relationship_interpreter",
    "parents-skills": "relationship_family_parents",
    "reunion-skill": "relationship_family_reunion",
    "MamaSkill": "relationship_family_mama",
    "digital-twin-skill": "digital_twin_high_fidelity",
    "immortal-skill": "digital_twin_immortal",
    "anti-distill": "protection_anti_distill",
}

REPO_URL_BY_SOURCE_REPO = {
    "self-skill": "https://github.com/moyitech/self-skill",
    "nuwa-skill": "https://github.com/alchaincyf/nuwa-skill",
    "forge-skill": "https://github.com/YIKUAIBANZI/forge-skill",
    "digital-life": "https://github.com/wildbyteai/digital-life",
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
    "parents-skills": "https://github.com/xiaoheizi8/parents-skills",
    "reunion-skill": "https://github.com/yangdongchen66-boop/reunion-skill",
    "MamaSkill": "https://github.com/jiangziyan-693/MamaSkill",
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
    "parents": "父母",
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
        "supervisor": "导师",
        "parents": "父母",
        "partner": "伴侣",
    },
}


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


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
    if normalized not in SUPPORTED_CREATE_TYPES:
        raise CreateWizardError(f"Unsupported create_type: {create_type}")
    return normalized


def _resolve_input_mode(create_type: str, source_repo: str, schema_key: str) -> str:
    if schema_key and schema_key in INPUT_MODE_LABELS.get(create_type, {}):
        return schema_key
    if source_repo and source_repo in INPUT_MODE_BY_SOURCE_REPO:
        return INPUT_MODE_BY_SOURCE_REPO[source_repo]
    if create_type == "self_persona":
        return "manual_profile"
    if create_type == "source_persona":
        return "documents"
    return "colleague"


def _resolve_schema_key(create_type: str, source_repo: str, input_mode: str, display_name: str) -> str:
    if source_repo and source_repo in SCHEMA_KEY_BY_SOURCE_REPO:
        return SCHEMA_KEY_BY_SOURCE_REPO[source_repo]
    fallback = f"{create_type}_{input_mode or 'default'}"
    return f"{fallback}_{_normalize_slug(display_name)}" if display_name else fallback


def _build_self_draft(form_data: dict[str, Any], display_name: str = "") -> dict[str, str]:
    name = _normalize_text(form_data.get("name")) or _normalize_text(display_name) or "我的自我人格"
    intro = _normalize_text(form_data.get("intro")) or "先把我自己的做事方式和表达方式整理出来。"
    values = _normalize_text(form_data.get("values")) or "先把重要的事做好，再让表达尽量清楚。"
    decision_priority = _normalize_text(form_data.get("decision_priority")) or "先看结果和可执行性。"
    expression_style = _normalize_text(form_data.get("expression_style")) or "直接、清楚、带一点解释。"
    boundaries = _normalize_text(form_data.get("boundaries")) or "保留个人边界，不越过自己不愿意暴露的部分。"

    profile = (
        f"{name} 的定位是一个从自己出发的自我人格。\n"
        f"简介：{intro}\n"
        f"最看重的东西：{values}"
    )
    mindset = _format_bullets(
        [
            f"遇到问题时先看 {decision_priority}",
            "先梳理目标，再判断路径是否可行",
            "信息不足时先补关键条件，而不是直接下结论",
        ]
    )
    heuristics = _format_bullets(
        [
            "先给一个能执行的版本，再补更理想的版本",
            "当选择过多时，优先筛掉代价高但收益低的选项",
            "如果目标和边界冲突，先保护边界，再调整方案",
        ]
    )
    expression = _format_bullets(
        [
            f"表达风格：{expression_style}",
            "回答时先说结论，再说理由",
            "适合拆成 3 到 4 个小点讲清楚",
        ]
    )
    guardrails = _format_bullets(
        [
            f"边界要求：{boundaries}",
            "不把不确定的内容说成确定事实",
            "不伪装成比实际更熟悉用户自己",
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


def build_persona_draft(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_create_type = _validate_create_type(payload.get("create_type", ""))
    config = CREATE_TYPE_CONFIG[normalized_create_type]

    normalized_group = _normalize_text(payload.get("group")) or config["group"]
    normalized_source_repo = _normalize_text(payload.get("source_repo")) or config["source_repo"]
    normalized_display_name = _normalize_text(payload.get("display_name")) or _normalize_text(payload.get("name"))
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

    if normalized_create_type == "self_persona":
        content = _build_self_draft(form_data, normalized_display_name)
    elif normalized_create_type == "source_persona":
        content = _build_source_draft(form_data, normalized_display_name)
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
        input_mode=normalized_input_mode,
        group=normalized_group,
        schema_key=normalized_schema_key,
        source_repo=normalized_source_repo,
        repo_url=REPO_URL_BY_SOURCE_REPO.get(normalized_source_repo, config["repo_url"]),
        source_repos=[normalized_source_repo] if normalized_source_repo else list(config["source_repos"]),
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
    }
