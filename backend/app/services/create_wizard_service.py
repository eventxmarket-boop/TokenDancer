from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.schemas.create_wizard import CreateWizardDraftMeta
from app.schemas.family_companion import (
    FamilyCompanionGuidedMemoryAnswers,
    FamilyCompanionMemoryBase,
    FamilyCompanionPersonaProfile,
)
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
from app.services import ocr_service
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


def _merge_unique_lines(*values: Any) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _clean_lines(value):
            if item and item not in seen:
                merged.append(item)
                seen.add(item)
    return merged


def _normalize_documents(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    documents: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            filename = _normalize_text(item.get("filename") or item.get("name"))
            content = _normalize_text(item.get("content") or item.get("text") or item.get("body"))
        else:
            filename = ""
            content = _normalize_text(item)

        if not filename and not content:
            continue

        documents.append({"filename": filename, "content": content})
    return documents


def _normalize_image_documents(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    documents: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            filename = _normalize_text(item.get("filename") or item.get("name"))
            mime_type = _normalize_text(item.get("mime_type") or item.get("type")) or "image/*"
            try:
                size = int(item.get("size") or 0)
            except (TypeError, ValueError):
                size = 0
            data_url = _normalize_text(item.get("data_url") or item.get("preview_url") or item.get("url"))
        else:
            filename = _normalize_text(item)
            mime_type = "image/*"
            size = 0
            data_url = ""

        if not filename and not data_url and not size:
            continue

        document = {
            "filename": filename,
            "mime_type": mime_type,
            "size": max(size, 0),
        }
        if data_url:
            document["data_url"] = data_url
        ocr_status = _normalize_text(item.get("ocr_status") or item.get("status"))
        if ocr_status:
            document["ocr_status"] = ocr_status
        ocr_text = _normalize_text(item.get("ocr_text") or item.get("text") or item.get("content"))
        if ocr_text:
            document["ocr_text"] = ocr_text
        documents.append(document)
    return documents


def _normalize_ocr_extracted_texts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    results: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            filename = _normalize_text(item.get("filename") or item.get("name"))
            mime_type = _normalize_text(item.get("mime_type") or item.get("type")) or "image/*"
            try:
                size = int(item.get("size") or 0)
            except (TypeError, ValueError):
                size = 0
            ocr_text = _normalize_text(item.get("ocr_text") or item.get("text") or item.get("content"))
            ocr_status = _normalize_text(item.get("ocr_status") or item.get("status")) or ("success" if ocr_text else "failed")
        else:
            filename = ""
            mime_type = "image/*"
            size = 0
            ocr_text = _normalize_text(item)
            ocr_status = "success" if ocr_text else "failed"

        if not filename and not ocr_text and not size:
            continue

        results.append(
            {
                "filename": filename,
                "mime_type": mime_type,
                "size": max(size, 0),
                "ocr_text": ocr_text,
                "ocr_status": ocr_status,
            }
        )
    return results


def _excerpt_text(value: Any, limit: int = 120) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    return text[:limit]


def _document_snippets(documents: list[dict[str, str]], *, limit: int = 2) -> list[str]:
    snippets: list[str] = []
    for doc in documents[:limit]:
        filename = _normalize_text(doc.get("filename"))
        content = _normalize_text(doc.get("content"))
        if not filename and not content:
            continue
        excerpt = content[:80]
        if filename and excerpt:
            snippets.append(f"{filename}：{excerpt}")
        elif filename:
            snippets.append(filename)
        else:
            snippets.append(excerpt)
    return [snippet for snippet in snippets if snippet]


def _select_material_summary(*parts: Any) -> str:
    snippets = [_excerpt_text(part, 48) for part in parts if _normalize_text(part)]
    snippets = [snippet for snippet in snippets if snippet]
    return " / ".join(snippets[:3])


def _has_meaningful_raw_materials(value: Any) -> bool:
    if not isinstance(value, dict):
        return False

    for item in value.values():
        if isinstance(item, list):
            if item:
                return True
            continue
        if isinstance(item, dict):
            if item:
                return True
            continue
        if _normalize_text(item):
            return True
    return False


def _raw_materials_payload(
    *,
    chat_history_text: Any = "",
    memory_notes_text: Any = "",
    text_materials_text: Any = "",
    uploaded_text_documents: Any = None,
    uploaded_image_documents: Any = None,
    ocr_extracted_texts: Any = None,
    image_notes_text: Any = "",
    voice_notes_text: Any = "",
    diary_text: Any = "",
    letter_text: Any = "",
    photo_notes_text: Any = "",
    conflict_text: Any = "",
    draft_message_text: Any = "",
    recent_context_text: Any = "",
    reply_style_samples_text: Any = "",
    relationship_status_text: Any = "",
    interaction_patterns_text: Any = "",
    history_text: Any = "",
    expression_samples_text: Any = "",
) -> dict[str, Any]:
    return {
        "chat_history_text": _normalize_text(chat_history_text),
        "memory_notes_text": _normalize_text(memory_notes_text),
        "text_materials_text": _normalize_text(text_materials_text),
        "uploaded_text_documents": _normalize_documents(uploaded_text_documents),
        "uploaded_image_documents": _normalize_image_documents(uploaded_image_documents),
        "ocr_extracted_texts": _normalize_ocr_extracted_texts(ocr_extracted_texts),
        "image_notes_text": _normalize_text(image_notes_text),
        "voice_notes_text": _normalize_text(voice_notes_text),
        "diary_text": _normalize_text(diary_text),
        "letter_text": _normalize_text(letter_text),
        "photo_notes_text": _normalize_text(photo_notes_text),
        "conflict_text": _normalize_text(conflict_text),
        "draft_message_text": _normalize_text(draft_message_text),
        "recent_context_text": _normalize_text(recent_context_text),
        "reply_style_samples_text": _normalize_text(reply_style_samples_text),
        "relationship_status_text": _normalize_text(relationship_status_text),
        "interaction_patterns_text": _normalize_text(interaction_patterns_text),
        "history_text": _normalize_text(history_text),
        "expression_samples_text": _normalize_text(expression_samples_text),
    }


def _collect_material_lines(*parts: Any) -> list[str]:
    lines: list[str] = []
    for part in parts:
        lines = _merge_unique_lines(lines, _clean_lines(part))
    return lines


def _material_summary_from_parts(*parts: Any) -> str:
    snippets = [_excerpt_text(part, 44) for part in parts if _normalize_text(part)]
    snippets = [snippet for snippet in snippets if snippet]
    return " / ".join(snippets[:3])


FAMILY_GUIDED_MEMORY_FIELDS = (
    "most_common_topics",
    "comfort_style",
    "most_characteristic_event",
    "repeated_phrases",
    "care_habits",
    "most_common_reminders",
)


def _normalize_guided_memory_answers(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}

    normalized: dict[str, str] = {}
    for field in FAMILY_GUIDED_MEMORY_FIELDS:
        text = _normalize_text(value.get(field))
        if text:
            normalized[field] = text
    return normalized


def _family_memory_layer_for_line(line: str, source_key: str = "") -> str:
    text = _normalize_text(line)
    source = _normalize_text(source_key)
    if not text and not source:
        return "semantic"

    episodic_hints = (
        "小时候",
        "一起",
        "回家",
        "团圆",
        "陪你",
        "家里",
        "过年",
        "那次",
        "那天",
        "第一次",
        "最后",
        "经历",
        "时刻",
        "事件",
        "记忆",
        "场景",
    )
    semantic_hints = (
        "建议",
        "提醒",
        "不要",
        "应该",
        "规则",
        "价值",
        "看重",
        "总是",
        "一直",
        "稳定",
        "先照顾",
        "先稳住",
        "家庭",
    )
    procedural_hints = (
        "会",
        "常常",
        "经常",
        "总会",
        "习惯",
        "怎么安慰",
        "怎么照顾",
        "口头禅",
        "语气",
        "节奏",
        "先别急",
        "慢慢来",
        "我在呢",
        "照顾",
        "关心",
    )

    scores = {
        "episodic": 0,
        "semantic": 0,
        "procedural": 0,
    }
    if source in {"shared_events", "memory_fragments", "chat_history_summary", "diary_text", "letter_text"}:
        scores["episodic"] += 1
    if source in {"important_advice", "emotional_triggers", "text_materials"}:
        scores["semantic"] += 1
    if source in {"daily_habits", "image_notes", "voice_notes"}:
        scores["procedural"] += 1

    if any(hint in text for hint in episodic_hints):
        scores["episodic"] += 3
    if any(hint in text for hint in semantic_hints):
        scores["semantic"] += 3
    if any(hint in text for hint in procedural_hints):
        scores["procedural"] += 3

    if "安慰" in text or "照顾" in text or "陪" in text:
        scores["procedural"] += 1
    if "提醒" in text or "建议" in text or "规则" in text:
        scores["semantic"] += 1
    if "一起" in text or "经历" in text or "记得" in text:
        scores["episodic"] += 1

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return ranked[0][0] if ranked else "semantic"


def _family_memory_base_dict(
    *,
    episodic_memories: Any = None,
    semantic_memories: Any = None,
    procedural_memories: Any = None,
    ocr_extracted_texts: Any = None,
    legacy_summary: Any = None,
    shared_events: Any = None,
    important_advice: Any = None,
    daily_habits: Any = None,
    emotional_triggers: Any = None,
    chat_history_summary: Any = "",
    memory_fragments: Any = None,
    text_materials: Any = None,
    image_notes: Any = None,
    voice_notes: Any = None,
) -> dict[str, Any]:
    episodic = _merge_unique_lines(episodic_memories)
    semantic = _merge_unique_lines(semantic_memories)
    procedural = _merge_unique_lines(procedural_memories)
    ocr_extracted_texts = _merge_unique_lines(ocr_extracted_texts)
    legacy = _merge_unique_lines(legacy_summary)

    shared_events = _merge_unique_lines(shared_events, episodic)
    important_advice = _merge_unique_lines(important_advice, semantic)
    daily_habits = _merge_unique_lines(daily_habits, procedural)
    emotional_triggers = _merge_unique_lines(emotional_triggers)
    memory_fragments = _merge_unique_lines(memory_fragments, episodic, semantic)
    text_materials = _merge_unique_lines(text_materials, semantic)
    image_notes = _merge_unique_lines(image_notes)
    voice_notes = _merge_unique_lines(voice_notes)
    legacy = _merge_unique_lines(
        legacy,
        episodic[:2],
        semantic[:2],
        procedural[:2],
        _clean_lines(chat_history_summary),
    )

    return {
        "episodic_memories": episodic,
        "semantic_memories": semantic,
        "procedural_memories": procedural,
        "ocr_extracted_texts": ocr_extracted_texts,
        "legacy_summary": legacy,
        "shared_events": shared_events,
        "important_advice": important_advice,
        "daily_habits": daily_habits,
        "emotional_triggers": emotional_triggers,
        "chat_history_summary": _normalize_text(chat_history_summary),
        "memory_fragments": memory_fragments,
        "text_materials": text_materials,
        "image_notes": image_notes,
        "voice_notes": voice_notes,
    }


def _family_memory_summary_excerpt(memory_base: dict[str, Any]) -> str:
    if not isinstance(memory_base, dict):
        return ""

    snippets = []
    for key in ("episodic_memories", "semantic_memories", "procedural_memories", "legacy_summary"):
        lines = _merge_unique_lines(memory_base.get(key))
        if lines:
            snippets.append(lines[0])
    return " / ".join(snippets[:3])


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


def _resolve_family_subtype(value: Any, relationship_type: Any = "", display_name: Any = "", input_mode: Any = "") -> str:
    normalized = _normalize_text(value).lower()
    normalized_relationship = _normalize_text(relationship_type)
    normalized_display = _normalize_text(display_name)
    normalized_input = _normalize_text(input_mode).lower()

    aliases = {
        "mother": "mother",
        "mama": "mother",
        "mom": "mother",
        "妈妈": "mother",
        "母亲": "mother",
        "parents": "parents",
        "parent": "parents",
        "father": "parents",
        "dad": "parents",
        "爸爸": "parents",
        "父亲": "parents",
        "父母": "parents",
        "other_family": "other_family",
        "other family": "other_family",
        "其他家人": "other_family",
    }
    if normalized in aliases:
        return aliases[normalized]
    if normalized_input in aliases:
        return aliases[normalized_input]
    if normalized_relationship in {"妈妈", "母亲"} or normalized_display in {"妈妈", "母亲"}:
        return "mother"
    if normalized_relationship in {"父母", "爸爸", "父亲"} or normalized_display in {"父母", "爸爸", "父亲"}:
        return "parents"
    if normalized_relationship == "其他家人" or normalized_display == "其他家人":
        return "other_family"
    return "mother"


def _family_subtype_label(subtype: str) -> str:
    subtype = _normalize_text(subtype)
    if subtype == "parents":
        return "父母"
    if subtype == "other_family":
        return "其他家人"
    return "妈妈"


def _family_subtype_profile_preset(subtype: str) -> dict[str, Any]:
    subtype = _resolve_family_subtype(subtype)
    if subtype == "parents":
        return {
            "focus": "更偏家庭整体视角、稳定建议和共同记忆",
            "tone": "更稳、更完整，带家庭整体视角。",
            "comfort_style": "先稳住情绪，再给更完整的家庭建议。",
            "celebration_style": "先一起高兴，再顺着把家里的安排和共识说完整。",
            "catchphrases": ["先稳住", "别急着下结论", "我们一起想办法"],
            "response_sequence": ["先看家庭整体处境", "再调用共同记忆", "再给稳定建议"],
            "memory_priority_rules": ["优先家庭共同记忆", "优先重要建议", "优先成长阶段记忆"],
        }
    if subtype == "other_family":
        return {
            "focus": "更偏通用家庭陪伴和自然关心",
            "tone": "温和、自然、通用家庭陪伴感。",
            "comfort_style": "先接住情绪，再给自然的陪伴和提醒。",
            "celebration_style": "先替你高兴，再顺着把好消息说完整。",
            "catchphrases": ["慢慢说", "我在呢", "先别急"],
            "response_sequence": ["先接住情绪", "再调用熟悉记忆", "再给自然回应"],
            "memory_priority_rules": ["优先常见关心方式", "优先共同经历", "优先日常提醒"],
        }
    return {
        "focus": "更偏接住情绪、细节照顾和熟悉安慰",
        "tone": "温和、亲近、会先接住情绪。",
        "comfort_style": "先接住情绪，再慢慢安慰，语气更熟悉。",
        "celebration_style": "先替你高兴，再顺着把好消息说完整。",
        "catchphrases": ["先别急", "慢慢来", "我在呢"],
        "response_sequence": ["先接住情绪", "再给熟悉的安慰", "再补一点日常照顾"],
        "memory_priority_rules": ["优先安慰方式", "优先关心细节", "优先日常提醒"],
    }


def build_family_persona_profile(
    form_data: dict[str, Any],
    display_name: str = "",
    input_mode: str = "",
    family_subtype: str = "",
    subtype_preset: dict[str, Any] | None = None,
) -> FamilyCompanionPersonaProfile:
    relation_type = (
        _normalize_text(form_data.get("relationship_type"))
        or RELATIONSHIP_LABELS.get(_normalize_text(input_mode), "")
        or _normalize_text(display_name)
        or "家人陪伴"
    )
    preset = subtype_preset or _family_subtype_profile_preset(family_subtype)
    return FamilyCompanionPersonaProfile(
        relationship_type=relation_type,
        name=_normalize_text(form_data.get("persona_name")) or _normalize_text(display_name) or relation_type,
        tone=_normalize_text(form_data.get("speech_style")) or preset["tone"],
        catchphrases=_clean_lines(form_data.get("catchphrases")) or list(preset["catchphrases"]),
        comfort_style=_normalize_text(form_data.get("comfort_style")) or preset["comfort_style"],
        celebration_style=_normalize_text(form_data.get("celebration_style")) or preset["celebration_style"],
        boundaries=_normalize_text(form_data.get("relation_boundaries")) or "不碰隐私边界，不越界替你做决定。",
    )


def build_family_emotion_rules(
    subtype: str,
    extraction_rules: dict[str, Any],
    subtype_preset: dict[str, Any],
) -> dict[str, Any]:
    family_subtype = _resolve_family_subtype(subtype)
    emotion_rules = dict(extraction_rules or {})
    summary = _normalize_text(emotion_rules.get("summary"))
    subtype_label = _family_subtype_label(family_subtype)
    emotion_rules["summary"] = (
        f"子类型：{subtype_label}；{subtype_preset.get('focus', '')}；{summary}"
        if summary
        else f"子类型：{subtype_label}；{subtype_preset.get('focus', '')}"
    ).strip("；")
    emotion_rules["subtype_label"] = subtype_label
    emotion_rules["subtype_focus"] = subtype_preset.get("focus", "")
    emotion_rules["response_sequence"] = _merge_unique_lines(
        subtype_preset["response_sequence"],
        emotion_rules.get("response_sequence"),
    )
    emotion_rules["memory_priority_rules"] = _merge_unique_lines(
        subtype_preset["memory_priority_rules"],
        emotion_rules.get("memory_priority_rules"),
    )
    emotion_rules["boundary_rules"] = _merge_unique_lines(
        emotion_rules.get("boundary_rules"),
        ["不伪造不确定的家庭事实", "不把关心变成控制"],
    )
    return emotion_rules


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
    name = _normalize_text(display_name) or _normalize_text(form_data.get("persona_name")) or relation_type
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


def extract_family_memory_base_from_materials(
    persona_form: dict[str, Any],
    memory_form: dict[str, Any],
    raw_materials: dict[str, Any],
) -> dict[str, Any]:
    persona_form = persona_form or {}
    memory_form = memory_form or {}
    raw_materials = raw_materials or {}

    relation_type = (
        _normalize_text(persona_form.get("relationship_type"))
        or _normalize_text(persona_form.get("persona_name"))
        or "家人陪伴"
    )
    tone = _normalize_text(persona_form.get("speech_style")) or "温和、亲近、稳一点。"
    comfort_style = _normalize_text(persona_form.get("comfort_style")) or "先接住情绪，再给安慰和陪伴。"
    celebration_style = _normalize_text(persona_form.get("celebration_style")) or "先替你高兴，再顺着把好消息说完整。"
    boundaries = _normalize_text(persona_form.get("relation_boundaries") or persona_form.get("boundaries")) or "不碰隐私边界，不越界替你做决定。"
    guided_answers = _normalize_guided_memory_answers(
        memory_form.get("guided_memory_answers")
        or persona_form.get("guided_memory_answers")
        or raw_materials.get("guided_memory_answers")
    )

    shared_events = _clean_lines(memory_form.get("shared_events") or persona_form.get("shared_events")) or [
        "小时候一起吃饭的场景",
        "你难过时被安慰的瞬间",
    ]
    important_advice = _clean_lines(memory_form.get("important_advice") or persona_form.get("important_advice")) or [
        "先照顾好自己",
        "遇到事先稳住再做决定",
    ]
    daily_habits = _clean_lines(memory_form.get("daily_habits") or persona_form.get("daily_habits")) or [
        "会关心你吃饭没",
        "会提醒你注意休息",
    ]
    emotional_triggers = _clean_lines(memory_form.get("emotional_triggers") or persona_form.get("emotional_triggers"))
    memory_fragments = _clean_lines(memory_form.get("memory_fragments") or persona_form.get("memory_fragments"))
    text_materials = _clean_lines(memory_form.get("text_materials") or persona_form.get("text_materials"))
    image_notes = _clean_lines(memory_form.get("image_notes") or persona_form.get("image_notes"))
    voice_notes = _clean_lines(memory_form.get("voice_notes") or persona_form.get("voice_notes"))
    ocr_extracted_texts = _clean_lines(
        [
            item.get("ocr_text")
            for item in raw_materials.get("ocr_extracted_texts", [])
            if isinstance(item, dict) and _normalize_text(item.get("ocr_text"))
        ]
    )
    episodic_memories: list[str] = []
    semantic_memories: list[str] = []
    procedural_memories: list[str] = []
    legacy_summary: list[str] = []

    material_lines = _merge_unique_lines(
        raw_materials.get("chat_history_text"),
        raw_materials.get("memory_notes_text"),
        raw_materials.get("text_materials_text"),
        raw_materials.get("image_notes_text"),
        raw_materials.get("voice_notes_text"),
        ocr_extracted_texts,
        [doc.get("content", "") for doc in raw_materials.get("uploaded_text_documents", []) if isinstance(doc, dict)],
    )
    if not raw_materials.get("chat_history_text"):
        raw_materials["chat_history_text"] = _select_material_summary(
            memory_form.get("chat_history_summary") or persona_form.get("chat_history_summary"),
            raw_materials.get("memory_notes_text"),
            raw_materials.get("text_materials_text"),
        )

    chat_history_summary = _normalize_text(raw_materials.get("chat_history_text"))
    if chat_history_summary:
        episodic_memories.append(chat_history_summary)
        legacy_summary.append(chat_history_summary)

    for line in material_lines:
        layer = _family_memory_layer_for_line(line, "materials")
        if layer == "episodic":
            shared_events.append(line)
            memory_fragments.append(line)
            episodic_memories.append(line)
        elif layer == "semantic":
            important_advice.append(line)
            text_materials.append(line)
            semantic_memories.append(line)
        else:
            daily_habits.append(line)
            procedural_memories.append(line)

        if any(keyword in line for keyword in ("难过", "开心", "高兴", "委屈", "压力", "担心", "焦虑")):
            emotional_triggers.append(line)
            legacy_summary.append(line)

    shared_events = _merge_unique_lines(shared_events)
    important_advice = _merge_unique_lines(important_advice)
    daily_habits = _merge_unique_lines(daily_habits)
    emotional_triggers = _merge_unique_lines(emotional_triggers)
    memory_fragments = _merge_unique_lines(memory_fragments, _document_snippets(raw_materials.get("uploaded_text_documents", [])))
    text_materials = _merge_unique_lines(text_materials, _document_snippets(raw_materials.get("uploaded_text_documents", [])))
    image_notes = _merge_unique_lines(image_notes)
    voice_notes = _merge_unique_lines(voice_notes)
    ocr_extracted_texts = _merge_unique_lines(ocr_extracted_texts)
    episodic_memories = _merge_unique_lines(episodic_memories, shared_events, memory_fragments)
    semantic_memories = _merge_unique_lines(semantic_memories, important_advice, text_materials, emotional_triggers)
    procedural_memories = _merge_unique_lines(procedural_memories, daily_habits, image_notes, voice_notes, ocr_extracted_texts)
    legacy_summary = _merge_unique_lines(
        legacy_summary,
        episodic_memories[:2],
        semantic_memories[:2],
        procedural_memories[:2],
    )

    memory_base = FamilyCompanionMemoryBase(
        episodic_memories=episodic_memories,
        semantic_memories=semantic_memories,
        procedural_memories=procedural_memories,
        legacy_summary=legacy_summary,
        shared_events=shared_events,
        important_advice=important_advice,
        daily_habits=daily_habits,
        emotional_triggers=emotional_triggers,
        chat_history_summary=chat_history_summary,
        memory_fragments=memory_fragments,
        text_materials=text_materials,
        image_notes=image_notes,
        voice_notes=voice_notes,
        ocr_extracted_texts=ocr_extracted_texts,
    )
    emotion_rules = {
        "summary": "先判断情绪，再提取记忆，再用家人的方式回应",
        "emotion_state_priority": [
            "难过 / 失落",
            "焦虑 / 压力",
            "开心 / 分享喜悦",
            "寻求建议",
            "日常聊天",
        ],
        "response_sequence": [
            "先接住当前情绪",
            "再调用熟悉记忆",
            "再给温和回应或建议",
        ],
        "response_temperature_map": {
            "难过 / 失落": "温暖、稳定、先接情绪",
            "焦虑 / 压力": "安抚但不空泛，先帮对方稳住",
            "开心 / 分享喜悦": "跟着高兴，顺着把好消息说完整",
            "寻求建议": "先安抚，再给具体建议",
            "日常聊天": "自然、熟悉、轻松",
        },
        "memory_priority_rules": [
            "优先使用从材料里提炼出的共同经历",
            "优先引用常说的话和典型关心方式",
            "优先贴近当前消息涉及的情绪关键词",
        ],
        "boundary_rules": _merge_unique_lines(
            [boundaries],
            ["不伪造不确定的家庭事实", "不把关心变成控制"],
        ),
    }
    return {
        "memory_base": memory_base.model_dump(),
        "emotion_rules": emotion_rules,
        "guided_memory_answers": guided_answers,
    }


def extract_family_memory_base_from_guided_answers(
    persona_form: dict[str, Any],
    guided_answers: dict[str, Any],
    raw_materials: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = persona_form or {}
    raw_materials = raw_materials or {}
    answers = _normalize_guided_memory_answers(guided_answers)
    if not answers:
        return {
            "memory_base": _family_memory_base_dict(
                chat_history_summary=_normalize_text(raw_materials.get("chat_history_text")),
            ),
            "guided_memory_answers": {},
        }

    episodic_memories: list[str] = []
    semantic_memories: list[str] = []
    procedural_memories: list[str] = []
    legacy_summary: list[str] = []
    shared_events: list[str] = []
    important_advice: list[str] = []
    daily_habits: list[str] = []
    emotional_triggers: list[str] = []
    memory_fragments: list[str] = []
    text_materials: list[str] = []

    source_map = {
        "most_common_topics": ("semantic", semantic_memories, legacy_summary, text_materials),
        "comfort_style": ("procedural", procedural_memories, legacy_summary, daily_habits),
        "most_characteristic_event": ("episodic", episodic_memories, legacy_summary, shared_events, memory_fragments),
        "repeated_phrases": ("procedural", procedural_memories, legacy_summary, daily_habits),
        "care_habits": ("procedural", procedural_memories, legacy_summary, daily_habits),
        "most_common_reminders": ("semantic", semantic_memories, legacy_summary, important_advice, emotional_triggers),
    }

    for field, value in answers.items():
        lines = _clean_lines(value)
        if not lines:
            continue
        layer_name, primary_bucket, summary_bucket, *extra_buckets = source_map.get(
            field,
            ("semantic", semantic_memories, legacy_summary),
        )
        primary_bucket.extend(lines)
        summary_bucket.extend(lines)
        for bucket in extra_buckets:
            bucket.extend(lines)
        if layer_name == "episodic":
            episodic_memories.extend(lines)
        elif layer_name == "procedural":
            procedural_memories.extend(lines)
        else:
            semantic_memories.extend(lines)

    memory_base = _family_memory_base_dict(
        episodic_memories=episodic_memories,
        semantic_memories=semantic_memories,
        procedural_memories=procedural_memories,
        ocr_extracted_texts=_clean_lines(
            [
                item.get("ocr_text")
                for item in raw_materials.get("ocr_extracted_texts", [])
                if isinstance(item, dict) and _normalize_text(item.get("ocr_text"))
            ]
        ),
        legacy_summary=legacy_summary,
        shared_events=shared_events or episodic_memories,
        important_advice=important_advice or semantic_memories,
        daily_habits=daily_habits or procedural_memories,
        emotional_triggers=emotional_triggers,
        chat_history_summary=_normalize_text(raw_materials.get("chat_history_text")),
        memory_fragments=memory_fragments or episodic_memories,
        text_materials=text_materials or semantic_memories,
    )
    return {
        "memory_base": memory_base,
        "guided_memory_answers": answers,
    }


def merge_family_memories(
    material_memory_base: dict[str, Any] | None,
    guided_memory_base: dict[str, Any] | None,
) -> dict[str, Any]:
    material_memory_base = material_memory_base or {}
    guided_memory_base = guided_memory_base or {}
    return _family_memory_base_dict(
        episodic_memories=_merge_unique_lines(
            material_memory_base.get("episodic_memories"),
            guided_memory_base.get("episodic_memories"),
        ),
        semantic_memories=_merge_unique_lines(
            material_memory_base.get("semantic_memories"),
            guided_memory_base.get("semantic_memories"),
        ),
        procedural_memories=_merge_unique_lines(
            material_memory_base.get("procedural_memories"),
            guided_memory_base.get("procedural_memories"),
        ),
        ocr_extracted_texts=_merge_unique_lines(
            material_memory_base.get("ocr_extracted_texts"),
            guided_memory_base.get("ocr_extracted_texts"),
        ),
        legacy_summary=_merge_unique_lines(
            material_memory_base.get("legacy_summary"),
            guided_memory_base.get("legacy_summary"),
        ),
        shared_events=_merge_unique_lines(
            material_memory_base.get("shared_events"),
            guided_memory_base.get("shared_events"),
        ),
        important_advice=_merge_unique_lines(
            material_memory_base.get("important_advice"),
            guided_memory_base.get("important_advice"),
        ),
        daily_habits=_merge_unique_lines(
            material_memory_base.get("daily_habits"),
            guided_memory_base.get("daily_habits"),
        ),
        emotional_triggers=_merge_unique_lines(
            material_memory_base.get("emotional_triggers"),
            guided_memory_base.get("emotional_triggers"),
        ),
        chat_history_summary=_normalize_text(
            material_memory_base.get("chat_history_summary") or guided_memory_base.get("chat_history_summary")
        ),
        memory_fragments=_merge_unique_lines(
            material_memory_base.get("memory_fragments"),
            guided_memory_base.get("memory_fragments"),
        ),
        text_materials=_merge_unique_lines(
            material_memory_base.get("text_materials"),
            guided_memory_base.get("text_materials"),
        ),
        image_notes=_merge_unique_lines(
            material_memory_base.get("image_notes"),
            guided_memory_base.get("image_notes"),
        ),
        voice_notes=_merge_unique_lines(
            material_memory_base.get("voice_notes"),
            guided_memory_base.get("voice_notes"),
        ),
    )


def build_family_companion_draft(
    form_data: dict[str, Any],
    display_name: str = "",
    input_mode: str = "",
    guided_memory_answers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw_materials_input = form_data.get("raw_materials") if isinstance(form_data.get("raw_materials"), dict) else {}
    family_subtype = _resolve_family_subtype(
        form_data.get("family_subtype") or input_mode or form_data.get("relationship_type") or display_name,
        form_data.get("relationship_type"),
        display_name,
        input_mode,
    )
    subtype_preset = _family_subtype_profile_preset(family_subtype)
    relation_type = (
        _normalize_text(form_data.get("relationship_type"))
        or RELATIONSHIP_LABELS.get(_normalize_text(input_mode), "")
        or _normalize_text(display_name)
        or "家人陪伴"
    )
    persona_profile = build_family_persona_profile(
        form_data,
        display_name=display_name,
        input_mode=input_mode,
        family_subtype=family_subtype,
        subtype_preset=subtype_preset,
    )

    raw_materials = _raw_materials_payload(
        chat_history_text=raw_materials_input.get("chat_history_text") or form_data.get("chat_history_summary"),
        memory_notes_text=raw_materials_input.get("memory_notes_text")
        or form_data.get("memory_fragments")
        or form_data.get("memory_notes"),
        text_materials_text=raw_materials_input.get("text_materials_text") or form_data.get("text_materials"),
        uploaded_text_documents=raw_materials_input.get("uploaded_text_documents")
        or form_data.get("uploaded_text_documents"),
        uploaded_image_documents=raw_materials_input.get("uploaded_image_documents")
        or form_data.get("uploaded_image_documents"),
        ocr_extracted_texts=raw_materials_input.get("ocr_extracted_texts") or form_data.get("ocr_extracted_texts"),
        image_notes_text=raw_materials_input.get("image_notes_text") or form_data.get("image_notes"),
        voice_notes_text=raw_materials_input.get("voice_notes_text") or form_data.get("voice_notes"),
    )
    existing_ocr_results = _normalize_ocr_extracted_texts(raw_materials.get("ocr_extracted_texts"))
    uploaded_image_documents = raw_materials.get("uploaded_image_documents") or []
    try:
        ocr_results = ocr_service.extract_texts_from_uploaded_images(uploaded_image_documents)
    except Exception:
        ocr_results = []

    def _merge_ocr_result(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base or {})
        for key in ("filename", "mime_type", "size", "ocr_status"):
            candidate_value = candidate.get(key)
            if key == "size":
                try:
                    size_value = int(candidate_value or merged.get(key) or 0)
                except (TypeError, ValueError):
                    size_value = int(merged.get(key) or 0)
                merged[key] = max(size_value, 0)
                continue
            if _normalize_text(candidate_value):
                merged[key] = candidate_value
            elif key not in merged:
                merged[key] = candidate_value
        candidate_text = _normalize_text(candidate.get("ocr_text"))
        if candidate_text:
            merged["ocr_text"] = candidate_text
        elif not _normalize_text(merged.get("ocr_text")):
            merged["ocr_text"] = _normalize_text(base.get("ocr_text"))
        if not _normalize_text(merged.get("ocr_status")):
            merged["ocr_status"] = "success" if _normalize_text(merged.get("ocr_text")) else "failed"
        return merged

    combined_ocr_results: list[dict[str, Any]] = []
    if existing_ocr_results or ocr_results:
        merged_by_filename: dict[str, dict[str, Any]] = {}
        for item in existing_ocr_results:
            filename = _normalize_text(item.get("filename"))
            if not filename:
                continue
            merged_by_filename[filename] = dict(item)
        for item in ocr_results:
            if not isinstance(item, dict):
                continue
            filename = _normalize_text(item.get("filename"))
            if filename and filename in merged_by_filename:
                merged_by_filename[filename] = _merge_ocr_result(merged_by_filename[filename], item)
            elif filename:
                merged_by_filename[filename] = dict(item)
            else:
                combined_ocr_results.append(dict(item))
        combined_ocr_results.extend(merged_by_filename.values())
    if uploaded_image_documents:
        raw_materials["uploaded_image_documents"] = ocr_service.attach_ocr_results_to_uploaded_images(
            uploaded_image_documents,
            combined_ocr_results,
        )
    raw_materials["ocr_extracted_texts"] = combined_ocr_results
    if uploaded_image_documents:
        attached_images = raw_materials.get("uploaded_image_documents") or []
        ocr_results_by_filename = {
            _normalize_text(item.get("filename")): item
            for item in ocr_results
            if isinstance(item, dict) and _normalize_text(item.get("filename"))
        }
        normalized_attached_images: list[dict[str, Any]] = []
        for index, document in enumerate(attached_images):
            if not isinstance(document, dict):
                continue
            merged_document = dict(document)
            result = ocr_results_by_filename.get(_normalize_text(merged_document.get("filename")))
            if not result and index < len(ocr_results) and isinstance(ocr_results[index], dict):
                result = ocr_results[index]
            if result:
                ocr_text = ocr_service.normalize_ocr_text(result.get("ocr_text") or result.get("text") or result.get("content"))
                if ocr_text:
                    merged_document["ocr_text"] = ocr_text
                    merged_document["ocr_status"] = _normalize_text(result.get("ocr_status") or result.get("status")) or "success"
            normalized_attached_images.append(merged_document)
        if normalized_attached_images:
            raw_materials["uploaded_image_documents"] = normalized_attached_images
    guided_answers_input = (
        guided_memory_answers
        if isinstance(guided_memory_answers, dict)
        else form_data.get("guided_memory_answers")
        if isinstance(form_data.get("guided_memory_answers"), dict)
        else {}
    )
    material_extraction = extract_family_memory_base_from_materials(form_data, form_data, raw_materials)
    guided_extraction = extract_family_memory_base_from_guided_answers(form_data, guided_answers_input, raw_materials)
    merged_memory_base = merge_family_memories(
        material_extraction.get("memory_base") or {},
        guided_extraction.get("memory_base") or {},
    )
    memory_base = FamilyCompanionMemoryBase.model_validate(merged_memory_base)
    emotion_rules = build_family_emotion_rules(
        family_subtype,
        material_extraction["emotion_rules"],
        subtype_preset,
    )

    name = _normalize_text(persona_profile.name) or _normalize_text(display_name) or relation_type
    tone = _normalize_text(persona_profile.tone) or subtype_preset["tone"]
    catchphrases = list(persona_profile.catchphrases or [])
    comfort_style = _normalize_text(persona_profile.comfort_style) or subtype_preset["comfort_style"]
    celebration_style = _normalize_text(persona_profile.celebration_style) or subtype_preset["celebration_style"]
    boundaries = _normalize_text(persona_profile.boundaries) or "不碰隐私边界，不越界替你做决定。"

    profile = (
        f"家人陪伴定位：{relation_type}\n"
        f"子类型：{_family_subtype_label(family_subtype)}\n"
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
        "family_subtype": family_subtype,
        "persona_profile": persona_profile.model_dump(),
        "memory_base": memory_base.model_dump(),
        "emotion_rules": emotion_rules,
        "raw_materials": raw_materials,
        "guided_memory_answers": guided_extraction.get("guided_memory_answers") or _normalize_guided_memory_answers(guided_answers_input),
        "name": name,
    }


def _build_reunion_persona_draft(
    form_data: dict[str, Any],
    display_name: str = "",
    input_mode: str = "",
) -> dict[str, Any]:
    raw_materials_input = form_data.get("raw_materials") if isinstance(form_data.get("raw_materials"), dict) else {}
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

    raw_materials = _raw_materials_payload(
        chat_history_text=raw_materials_input.get("chat_history_text") or form_data.get("chat_history_summary"),
        diary_text=raw_materials_input.get("diary_text") or form_data.get("diary_notes"),
        letter_text=raw_materials_input.get("letter_text") or form_data.get("letter_notes"),
        memory_notes_text=raw_materials_input.get("memory_notes_text")
        or form_data.get("memory_fragments")
        or form_data.get("memory_notes"),
        uploaded_text_documents=raw_materials_input.get("uploaded_text_documents")
        or form_data.get("uploaded_text_documents"),
        photo_notes_text=raw_materials_input.get("photo_notes_text") or form_data.get("photo_notes"),
        voice_notes_text=raw_materials_input.get("voice_notes_text") or form_data.get("voice_notes"),
    )
    material_lines = _merge_unique_lines(
        raw_materials["chat_history_text"],
        raw_materials["diary_text"],
        raw_materials["letter_text"],
        raw_materials["memory_notes_text"],
        raw_materials["photo_notes_text"],
        raw_materials["voice_notes_text"],
        [doc.get("content", "") for doc in raw_materials["uploaded_text_documents"]],
    )

    if not raw_materials["chat_history_text"]:
        raw_materials["chat_history_text"] = _select_material_summary(
            form_data.get("chat_history_summary"),
            raw_materials["diary_text"],
            raw_materials["letter_text"],
            raw_materials["memory_notes_text"],
        )

    for line in material_lines:
        if any(keyword in line for keyword in ("记得", "以前", "从前", "过去", "曾经", "重逢", "再见", "怀念", "想念")):
            shared_memories.append(line)
        else:
            memory_fragments.append(line)

    diary_notes = _merge_unique_lines(diary_notes)
    letter_notes = _merge_unique_lines(letter_notes)
    photo_notes = _merge_unique_lines(photo_notes)
    voice_notes = _merge_unique_lines(voice_notes)
    memory_fragments = _merge_unique_lines(memory_fragments, _document_snippets(raw_materials["uploaded_text_documents"]))
    shared_memories = _merge_unique_lines(shared_memories)
    chat_history_summary = _normalize_text(raw_materials["chat_history_text"])

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
        "raw_materials": raw_materials,
        "name": name,
    }


def _build_intimate_companion_draft(
    form_data: dict[str, Any],
    display_name: str = "",
    input_mode: str = "",
) -> dict[str, Any]:
    mode = _normalize_text(input_mode) or "relationship_understanding"
    raw_materials_input = form_data.get("raw_materials") if isinstance(form_data.get("raw_materials"), dict) else {}
    relation_type = (
        _normalize_text(form_data.get("relationship_type"))
        or RELATIONSHIP_LABELS.get(mode, "")
        or _normalize_text(display_name)
        or "亲密关系"
    )
    name = _normalize_text(form_data.get("persona_name")) or _normalize_text(display_name) or relation_type
    relationship_stage = _normalize_text(form_data.get("relationship_stage")) or "关系阶段待补充"
    tone = _normalize_text(form_data.get("speech_style")) or "自然、亲近、带一点熟悉感。"
    response_temperature = _normalize_text(form_data.get("response_temperature")) or "先接住情绪，再顺着回应。"
    catchphrases = _clean_lines(form_data.get("catchphrases")) or ["最近怎么样", "我在听"]
    boundaries = _normalize_text(form_data.get("relation_boundaries")) or "不越界，不替对方下结论。"

    raw_materials = _raw_materials_payload(
        chat_history_text=raw_materials_input.get("chat_history_text") or form_data.get("chat_history_summary"),
        memory_notes_text=raw_materials_input.get("memory_notes_text") or form_data.get("memory_fragments"),
        text_materials_text=raw_materials_input.get("text_materials_text") or form_data.get("text_materials"),
        uploaded_text_documents=raw_materials_input.get("uploaded_text_documents")
        or form_data.get("uploaded_text_documents"),
        image_notes_text=raw_materials_input.get("image_notes_text") or form_data.get("image_notes"),
        voice_notes_text=raw_materials_input.get("voice_notes_text") or form_data.get("voice_notes"),
        conflict_text=raw_materials_input.get("conflict_text") or form_data.get("memory_fragments"),
        draft_message_text=raw_materials_input.get("draft_message_text") or form_data.get("conversation_samples"),
        recent_context_text=raw_materials_input.get("recent_context_text") or form_data.get("chat_history_summary"),
        reply_style_samples_text=raw_materials_input.get("reply_style_samples_text") or form_data.get("conversation_samples"),
        relationship_status_text=raw_materials_input.get("relationship_status_text") or form_data.get("relationship_stage"),
        interaction_patterns_text=raw_materials_input.get("interaction_patterns_text") or form_data.get("interaction_rules"),
        history_text=raw_materials_input.get("history_text") or form_data.get("key_memories"),
        expression_samples_text=raw_materials_input.get("expression_samples_text") or form_data.get("catchphrases"),
    )

    relationship_context = {
        "relationship_type": relation_type,
        "name": name,
        "relationship_stage": relationship_stage,
        "speech_style": tone,
        "boundaries": boundaries,
        "focus": _normalize_text(form_data.get("purpose"))
        or _normalize_text(form_data.get("decision_logic"))
        or "根据场景提炼更合适的回应方式。",
    }

    base_conversation_samples = _merge_unique_lines(
        _clean_lines(form_data.get("conversation_samples")),
        _collect_material_lines(
            raw_materials["chat_history_text"],
            raw_materials["recent_context_text"],
            raw_materials["draft_message_text"],
            raw_materials["reply_style_samples_text"],
        ),
        _document_snippets(raw_materials["uploaded_text_documents"]),
    )
    base_memory_fragments = _merge_unique_lines(
        _clean_lines(form_data.get("memory_fragments")),
        _collect_material_lines(
            raw_materials["memory_notes_text"],
            raw_materials["conflict_text"],
            raw_materials["text_materials_text"],
        ),
        _document_snippets(raw_materials["uploaded_text_documents"]),
    )
    base_interaction_rules = _merge_unique_lines(
        _clean_lines(form_data.get("interaction_rules")),
        _collect_material_lines(
            raw_materials["interaction_patterns_text"],
            raw_materials["reply_style_samples_text"],
        ),
    )
    base_relationship_goals = _merge_unique_lines(
        _clean_lines(form_data.get("relationship_goals")),
        _collect_material_lines(
            raw_materials["draft_message_text"],
            raw_materials["relationship_status_text"],
        ),
    )
    base_key_memories = _merge_unique_lines(
        _clean_lines(form_data.get("key_memories")),
        _collect_material_lines(
            raw_materials["history_text"],
            raw_materials["text_materials_text"],
        ),
        _document_snippets(raw_materials["uploaded_text_documents"]),
    )
    base_expression_samples = _merge_unique_lines(
        _clean_lines(form_data.get("catchphrases")),
        _collect_material_lines(
            raw_materials["expression_samples_text"],
            raw_materials["reply_style_samples_text"],
        ),
    )

    if mode == "relationship_understanding":
        relationship_profile = {
            "relationship_type": relation_type,
            "name": name,
            "relationship_stage": relationship_stage,
            "tone": tone,
            "response_temperature": response_temperature,
            "catchphrases": catchphrases,
            "boundaries": boundaries,
        }
        conversation_samples = _merge_unique_lines(
            base_conversation_samples,
            _collect_material_lines(
                raw_materials["chat_history_text"],
                raw_materials["memory_notes_text"],
                raw_materials["text_materials_text"],
            ),
            _document_snippets(raw_materials["uploaded_text_documents"]),
        )
        misunderstanding_points = _merge_unique_lines(
            base_memory_fragments,
            _collect_material_lines(
                raw_materials["conflict_text"],
                raw_materials["recent_context_text"],
            ),
        )
        rewrite_targets = _merge_unique_lines(
            base_relationship_goals,
            _collect_material_lines(
                raw_materials["draft_message_text"],
                raw_materials["reply_style_samples_text"],
            ),
        )
        memory_base = IntimateCompanionMemoryBase(
            conversation_samples=conversation_samples,
            interaction_rules=_merge_unique_lines(base_interaction_rules, ["先看关系阶段，再判断沟通卡点"]),
            relationship_goals=base_relationship_goals,
            key_memories=base_key_memories,
            relationship_context=_material_summary_from_parts(
                relation_type,
                relationship_stage,
                tone,
                raw_materials["chat_history_text"],
            ),
            misunderstanding_points=misunderstanding_points,
            rewrite_targets=rewrite_targets,
            target_persona_profile=relationship_profile,
            conversation_context={
                "relationship_stage": relationship_stage,
                "focus": relationship_context["focus"],
                "mode": mode,
            },
            reply_style_samples=base_expression_samples,
            simulation_preferences={},
            interaction_patterns=base_interaction_rules,
            maintenance_goals=base_relationship_goals,
            relationship_memory=base_key_memories,
            expression_samples=base_expression_samples,
            response_temperature=response_temperature,
            boundaries=_clean_lines(boundaries),
        )
        profile = (
            f"亲密关系定位：{relation_type}\n"
            f"对象名称：{name}\n"
            f"关系阶段：{relationship_stage}\n"
            f"说话风格：{tone}\n"
            f"用途：输入聊天样本、冲突片段和待改写消息，先看理解和改写方向。"
        )
        mindset = _format_bullets(
            [
                "先看关系阶段和沟通卡点，再判断对方表达的意思",
                "先把误解点和改写目标理清，再给建议",
                "信息不足时先补聊天样本和冲突片段",
            ]
        )
        heuristics = _format_bullets(
            [
                "优先识别关系阶段、情绪状态与沟通意图",
                "改写建议要贴近真实聊天样本",
                "不要把单条消息直接推成全部关系结论",
            ]
        )
        expression = _format_bullets(
            [
                f"理解视角：{relationship_context['focus']}",
                f"说话风格：{tone}",
                "回答要像先分析关系，再给改写建议",
            ]
        )
        guardrails = _format_bullets(
            [
                f"边界要求：{boundaries}",
                "不伪造未确认的关系事实",
                "不把推测写成确定判断",
            ]
        )
        return {
            "profile": profile,
            "mindset": mindset,
            "heuristics": heuristics,
            "expression": expression,
            "guardrails": guardrails,
            "relationship_type": relation_type,
            "relationship_profile": relationship_profile,
            "intimate_memory_base": memory_base.model_dump(),
            "intimate_understanding": {
                "relationship_context": relationship_context,
                "conversation_samples": conversation_samples,
                "misunderstanding_points": misunderstanding_points,
                "rewrite_targets": rewrite_targets,
                "raw_materials": raw_materials,
            },
            "raw_materials": raw_materials,
            "name": name,
        }

    if mode == "message_simulation":
        target_persona_profile = {
            "relationship_type": relation_type,
            "name": name,
            "speech_style": tone,
            "response_temperature": response_temperature,
            "boundaries": boundaries,
            "stage": relationship_stage,
        }
        conversation_context = {
            "recent_context": _normalize_text(raw_materials["recent_context_text"])
            or _normalize_text(form_data.get("chat_history_summary")),
            "current_message": _normalize_text(raw_materials["draft_message_text"])
            or _normalize_text(form_data.get("conversation_samples")),
            "relationship_stage": relationship_stage,
        }
        reply_style_samples = _merge_unique_lines(
            _clean_lines(form_data.get("conversation_samples")),
            _collect_material_lines(
                raw_materials["reply_style_samples_text"],
                raw_materials["chat_history_text"],
            ),
            _document_snippets(raw_materials["uploaded_text_documents"]),
        )
        simulation_preferences = {
            "candidate_count": 3,
            "tone": tone,
            "response_temperature": response_temperature,
            "mode": mode,
        }
        memory_base = IntimateCompanionMemoryBase(
            conversation_samples=_merge_unique_lines(
                base_conversation_samples,
                reply_style_samples,
            ),
            interaction_rules=_merge_unique_lines(base_interaction_rules, ["先给 2~4 个候选回复，再给建议发送版本"]),
            relationship_goals=_merge_unique_lines(base_relationship_goals, ["更像对方的表达节奏"]),
            key_memories=base_key_memories,
            relationship_context=_material_summary_from_parts(
                relation_type,
                relationship_stage,
                tone,
                raw_materials["chat_history_text"],
            ),
            misunderstanding_points=base_memory_fragments,
            rewrite_targets=base_relationship_goals,
            target_persona_profile=target_persona_profile,
            conversation_context=conversation_context,
            reply_style_samples=reply_style_samples,
            simulation_preferences=simulation_preferences,
            interaction_patterns=base_interaction_rules,
            maintenance_goals=[],
            relationship_memory=base_key_memories,
            expression_samples=base_expression_samples,
            response_temperature=response_temperature,
            boundaries=_clean_lines(boundaries),
        )
        profile = (
            f"消息模拟定位：{relation_type}\n"
            f"对象名称：{name}\n"
            f"说话风格：{tone}\n"
            f"回复温度：{response_temperature}\n"
            f"用途：输入当前消息和最近上下文，预测 2~4 个候选回复。"
        )
        mindset = _format_bullets(
            [
                "先看最近上下文，再判断对方可能的回复节奏",
                "先保留对方一贯的说话习惯，再做候选分支",
                "信息不足时先补聊天样本和语气样本",
            ]
        )
        heuristics = _format_bullets(
            [
                "优先给出多个候选回复，再给建议版本",
                "候选回复尽量贴近对方样本里的语气",
                "不要把单条消息误判成全部关系状态",
            ]
        )
        expression = _format_bullets(
            [
                f"候选回复语气：{tone}",
                f"回复温度：{response_temperature}",
                "输出要像发送前预演，而不是泛建议",
            ]
        )
        guardrails = _format_bullets(
            [
                f"边界要求：{boundaries}",
                "不伪造未确认的回复",
                "不把候选分支写成唯一真相",
            ]
        )
        return {
            "profile": profile,
            "mindset": mindset,
            "heuristics": heuristics,
            "expression": expression,
            "guardrails": guardrails,
            "relationship_type": relation_type,
            "relationship_profile": target_persona_profile,
            "intimate_memory_base": memory_base.model_dump(),
            "intimate_message_simulation": {
                "target_persona_profile": target_persona_profile,
                "conversation_context": conversation_context,
                "reply_style_samples": reply_style_samples,
                "simulation_preferences": simulation_preferences,
                "raw_materials": raw_materials,
            },
            "raw_materials": raw_materials,
            "name": name,
        }

    if mode == "partner_maintenance":
        relationship_profile = {
            "relationship_type": relation_type,
            "name": name,
            "relationship_stage": relationship_stage,
            "tone": tone,
            "response_temperature": response_temperature,
            "catchphrases": catchphrases,
            "boundaries": boundaries,
        }
        interaction_patterns = _merge_unique_lines(
            _clean_lines(form_data.get("interaction_rules")),
            _collect_material_lines(
                raw_materials["interaction_patterns_text"],
                raw_materials["chat_history_text"],
                raw_materials["memory_notes_text"],
            ),
        )
        maintenance_goals = _merge_unique_lines(
            _clean_lines(form_data.get("relationship_goals")),
            _collect_material_lines(
                raw_materials["relationship_status_text"],
                raw_materials["draft_message_text"],
            ),
        )
        conversation_samples = _merge_unique_lines(
            base_conversation_samples,
            _collect_material_lines(
                raw_materials["chat_history_text"],
                raw_materials["recent_context_text"],
            ),
        )
        memory_base = IntimateCompanionMemoryBase(
            conversation_samples=conversation_samples,
            interaction_rules=interaction_patterns,
            relationship_goals=maintenance_goals,
            key_memories=base_key_memories,
            relationship_context=_material_summary_from_parts(
                relation_type,
                relationship_stage,
                tone,
                raw_materials["chat_history_text"],
            ),
            misunderstanding_points=base_memory_fragments,
            rewrite_targets=maintenance_goals,
            target_persona_profile=relationship_profile,
            conversation_context={"relationship_stage": relationship_stage, "mode": mode},
            reply_style_samples=base_expression_samples,
            simulation_preferences={},
            interaction_patterns=interaction_patterns,
            maintenance_goals=maintenance_goals,
            relationship_memory=base_key_memories,
            expression_samples=base_expression_samples,
            response_temperature=response_temperature,
            boundaries=_clean_lines(boundaries),
        )
        profile = (
            f"关系维护定位：{relation_type}\n"
            f"对象名称：{name}\n"
            f"关系阶段：{relationship_stage}\n"
            f"说话风格：{tone}\n"
            f"用途：围绕伴侣关系维护、磨合和沟通修复整理人格。"
        )
        mindset = _format_bullets(
            [
                "先看关系互动模式，再决定是修复、安抚还是推进",
                "先保留关系中的稳定信号，再处理冲突点",
                "信息不足时先补关系样本和常见冲突",
            ]
        )
        heuristics = _format_bullets(
            [
                "优先看长期互动模式，不只看一次争执",
                "修复建议要贴近伴侣关系语境",
                "如果目标不清楚，先回到关系目标再继续",
            ]
        )
        expression = _format_bullets(
            [
                f"常见说话感觉：{tone}",
                f"回复温度：{response_temperature}",
                "回答要像关系维护建议，不要像普通陪聊",
            ]
        )
        guardrails = _format_bullets(
            [
                f"边界要求：{boundaries}",
                "不把冲突细节夸大成唯一结论",
                "不越界替对方下判断",
            ]
        )
        return {
            "profile": profile,
            "mindset": mindset,
            "heuristics": heuristics,
            "expression": expression,
            "guardrails": guardrails,
            "relationship_type": relation_type,
            "relationship_profile": relationship_profile,
            "intimate_memory_base": memory_base.model_dump(),
            "intimate_relationship_maintenance": {
                "relationship_profile": relationship_profile,
                "interaction_patterns": interaction_patterns,
                "maintenance_goals": maintenance_goals,
                "conversation_samples": conversation_samples,
                "raw_materials": raw_materials,
            },
            "raw_materials": raw_materials,
            "name": name,
        }

    if mode == "past_relation_mirror":
        persona_profile = {
            "relationship_type": relation_type,
            "name": name,
            "tone": tone,
            "remembrance_style": _normalize_text(form_data.get("remembrance_style")) or "先慢慢回忆，再一点点靠近。",
            "response_temperature": response_temperature,
            "boundaries": boundaries,
        }
        relationship_memory = _merge_unique_lines(
            _clean_lines(form_data.get("key_memories")),
            _collect_material_lines(
                raw_materials["chat_history_text"],
                raw_materials["memory_notes_text"],
                raw_materials["history_text"],
                raw_materials["text_materials_text"],
            ),
            _document_snippets(raw_materials["uploaded_text_documents"]),
        )
        expression_samples = _merge_unique_lines(
            _clean_lines(form_data.get("catchphrases")),
            _collect_material_lines(
                raw_materials["expression_samples_text"],
                raw_materials["reply_style_samples_text"],
            ),
        )
        memory_base = IntimateCompanionMemoryBase(
            conversation_samples=_merge_unique_lines(
                base_conversation_samples,
                _collect_material_lines(raw_materials["chat_history_text"], raw_materials["history_text"]),
            ),
            interaction_rules=_merge_unique_lines(base_interaction_rules, ["先克制，再回忆", "不激进刺激"]),
            relationship_goals=_merge_unique_lines(base_relationship_goals, ["保留情绪边界", "慢慢靠近记忆"]),
            key_memories=relationship_memory,
            relationship_context=_material_summary_from_parts(
                relation_type,
                persona_profile["remembrance_style"],
                tone,
                raw_materials["chat_history_text"],
            ),
            misunderstanding_points=base_memory_fragments,
            rewrite_targets=base_relationship_goals,
            target_persona_profile=persona_profile,
            conversation_context={"mode": mode, "boundary": boundaries},
            reply_style_samples=expression_samples,
            simulation_preferences={},
            interaction_patterns=base_interaction_rules,
            maintenance_goals=base_relationship_goals,
            relationship_memory=relationship_memory,
            expression_samples=expression_samples,
            response_temperature=response_temperature,
            boundaries=_clean_lines(boundaries),
        )
        profile = (
            f"过去关系 / 自我镜像定位：{relation_type}\n"
            f"称呼：{name}\n"
            f"回忆方式：{persona_profile['remembrance_style']}\n"
            f"说话风格：{tone}\n"
            f"用途：整理历史关系、镜像自我表达与克制的陪伴回应。"
        )
        mindset = _format_bullets(
            [
                "先判断是回忆、复盘还是自我支持，再决定回应节奏",
                "先从少量相关记忆开始，再逐步靠近细节",
                "信息不足时先补材料来源和边界",
            ]
        )
        heuristics = _format_bullets(
            [
                "优先采用渐进式回忆",
                "自我镜像时优先保留自己的表达习惯",
                "不要把怀念推成失控刺激",
            ]
        )
        expression = _format_bullets(
            [
                f"常见说话感觉：{tone}",
                f"回忆节奏：{persona_profile['remembrance_style']}",
                "回答要克制、带记忆感，但不过度刺激情绪",
            ]
        )
        guardrails = _format_bullets(
            [
                f"边界要求：{boundaries}",
                "不伪造未确认的历史细节",
                "不把过去关系写成现实替代",
            ]
        )
        return {
            "profile": profile,
            "mindset": mindset,
            "heuristics": heuristics,
            "expression": expression,
            "guardrails": guardrails,
            "relationship_type": relation_type,
            "relationship_profile": persona_profile,
            "intimate_memory_base": memory_base.model_dump(),
            "intimate_past_relationship": {
                "persona_profile": persona_profile,
                "relationship_memory": relationship_memory,
                "expression_samples": expression_samples,
                "response_temperature": response_temperature,
                "boundaries": _clean_lines(boundaries),
                "raw_materials": raw_materials,
            },
            "raw_materials": raw_materials,
            "name": name,
        }

    conversation_samples = _merge_unique_lines(
        _clean_lines(form_data.get("conversation_samples")),
        base_conversation_samples,
    )
    interaction_rules = _merge_unique_lines(
        _clean_lines(form_data.get("interaction_rules")),
        base_interaction_rules,
    )
    relationship_goals = _merge_unique_lines(
        _clean_lines(form_data.get("relationship_goals")),
        base_relationship_goals,
    )
    key_memories = _merge_unique_lines(
        _clean_lines(form_data.get("key_memories")),
        base_key_memories,
    )

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
        relationship_context=_material_summary_from_parts(
            relation_type,
            relationship_stage,
            tone,
            raw_materials["chat_history_text"],
        ),
        misunderstanding_points=base_memory_fragments,
        rewrite_targets=relationship_goals,
        target_persona_profile={},
        conversation_context={},
        reply_style_samples=base_expression_samples,
        simulation_preferences={},
        interaction_patterns=interaction_rules,
        maintenance_goals=relationship_goals,
        relationship_memory=key_memories,
        expression_samples=base_expression_samples,
        response_temperature=response_temperature,
        boundaries=_clean_lines(boundaries),
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
        "raw_materials": raw_materials,
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
    payload_raw_materials = payload.get("raw_materials")
    if isinstance(payload_raw_materials, dict) and _has_meaningful_raw_materials(payload_raw_materials):
        merged_raw_materials = {}
        if isinstance(form_data.get("raw_materials"), dict):
            merged_raw_materials.update(form_data.get("raw_materials") or {})
        merged_raw_materials.update(payload_raw_materials)
        form_data = {**form_data, "raw_materials": merged_raw_materials}
    family_subtype = _normalize_text(payload.get("family_subtype")) or _normalize_text(form_data.get("family_subtype"))
    if normalized_create_type == "family_companion" and family_subtype:
        form_data = {**form_data, "family_subtype": family_subtype}
    guided_memory_answers = _normalize_guided_memory_answers(payload.get("guided_memory_answers"))
    form_guided_memory_answers = _normalize_guided_memory_answers(form_data.get("guided_memory_answers"))
    if form_guided_memory_answers:
        guided_memory_answers = {**form_guided_memory_answers, **guided_memory_answers}

    if normalized_create_type == "self_unified":
        content = _build_self_draft(form_data, normalized_display_name)
    elif normalized_create_type == "source_persona":
        content = _build_source_draft(form_data, normalized_display_name)
    elif normalized_create_type == "family_companion":
        content = build_family_companion_draft(
            form_data,
            normalized_display_name,
            normalized_input_mode,
            guided_memory_answers,
        )
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
        family_subtype=family_subtype if normalized_create_type == "family_companion" else "",
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
        "family_subtype": content.get("family_subtype", ""),
        "raw_materials": content.get("raw_materials"),
        "guided_memory_answers": content.get("guided_memory_answers"),
        "emotion_rules": content.get("emotion_rules"),
        "self_persona_unified": content.get("self_persona_unified"),
        "persona_profile": content.get("persona_profile"),
        "memory_base": content.get("memory_base"),
        "reunion_persona_profile": content.get("reunion_persona_profile"),
        "reunion_memory_base": content.get("reunion_memory_base"),
        "reunion_memory_retrieval_policy": content.get("reunion_memory_retrieval_policy"),
        "reunion_safety_guardrails": content.get("reunion_safety_guardrails"),
        "relationship_profile": content.get("relationship_profile"),
        "intimate_memory_base": content.get("intimate_memory_base"),
        "intimate_understanding": content.get("intimate_understanding"),
        "intimate_message_simulation": content.get("intimate_message_simulation"),
        "intimate_relationship_maintenance": content.get("intimate_relationship_maintenance"),
        "intimate_past_relationship": content.get("intimate_past_relationship"),
    }
