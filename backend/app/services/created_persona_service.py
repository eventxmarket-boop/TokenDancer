from __future__ import annotations

import json
import re
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.created_persona import CreatedPersona
from app.schemas.create_wizard import CreateWizardDraft
from app.services import ocr_service


class CreatedPersonaError(RuntimeError):
    pass


class CreatedPersonaNotFoundError(CreatedPersonaError):
    pass


_PERSONA_TYPE_LABELS = {
    "self_unified": "我的人格",
    "self_persona": "我的人格",
    "source_persona": "资料",
    "relationship_persona": "关系",
    "intimate_companion": "亲密关系",
    "family_companion": "家人陪伴",
    "reunion_persona": "重逢人格",
}

_SELF_UNIFIED_ALIASES = {
    "self_persona",
    "self_mindset_distill",
    "self_deep_self_persona",
    "self_digital_trace_persona",
}

_INTIMATE_MODE_LABELS = {
    "relationship_understanding": "关系理解",
    "message_simulation": "消息模拟",
    "partner_maintenance": "关系维护",
    "past_relation_mirror": "过去关系 / 自我镜像",
}

_FAMILY_SUBTYPE_LABELS = {
    "mother": "妈妈",
    "parents": "父母",
    "other_family": "其他家人",
}


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _clean_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_text(value)
    if not text:
        return []
    return [line.strip("•- \t") for line in text.splitlines() if line.strip()]


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


def _normalize_ocr_results(value: Any) -> list[dict[str, Any]]:
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


def _excerpt_text(value: Any, limit: int = 48) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    return text[:limit]


def _family_subtype_label(value: Any) -> str:
    subtype = _normalize_text(value)
    return _FAMILY_SUBTYPE_LABELS.get(subtype, subtype)


def _material_summary_from_raw_materials(raw_materials: Any) -> str:
    if not isinstance(raw_materials, dict):
        return ""

    parts: list[str] = []
    documents = _normalize_documents(raw_materials.get("uploaded_text_documents"))
    if documents:
        doc_items: list[str] = []
        for document in documents[:2]:
            filename = _normalize_text(document.get("filename"))
            content = _normalize_text(document.get("content"))
            snippet = content[:16]
            if filename:
                doc_items.append(filename)
            elif snippet:
                doc_items.append(snippet)
        if doc_items:
            parts.append(f"文件材料：{' / '.join(doc_items)}")
        else:
            parts.append(f"文件材料：{len(documents)} 份")

    image_documents = _normalize_image_documents(raw_materials.get("uploaded_image_documents"))
    if image_documents:
        parts.append(f"图片材料：{len(image_documents)} 张")
        first_image = image_documents[0]
        ocr_status = _normalize_text(first_image.get("ocr_status"))
        if ocr_status:
            parts.append(f"首图识别：{ocr_status}")

    ocr_results = _normalize_ocr_results(raw_materials.get("ocr_extracted_texts"))
    if ocr_results:
        summary = ocr_service.summarize_ocr_results(ocr_results)
        if summary:
            parts.append(summary)

    chat_history = _excerpt_text(raw_materials.get("chat_history_text"), 40)
    if chat_history:
        parts.append(f"聊天记录：{chat_history}")

    text_notes = _excerpt_text(
        raw_materials.get("memory_notes_text")
        or raw_materials.get("text_materials_text")
        or raw_materials.get("diary_text")
        or raw_materials.get("letter_text"),
        40,
    )
    if text_notes:
        parts.append(f"文本材料：{text_notes}")

    image_notes = _excerpt_text(raw_materials.get("image_notes_text") or raw_materials.get("photo_notes_text"), 30)
    if image_notes:
        parts.append(f"图片说明：{image_notes}")

    voice_notes = _excerpt_text(raw_materials.get("voice_notes_text"), 30)
    if voice_notes:
        parts.append(f"语音说明：{voice_notes}")

    return "；".join(parts[:5])


def _object_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _family_memory_layer_summary(memory: Any) -> str:
    if memory is None:
        return ""

    episodic = _clean_lines(_object_value(memory, "episodic_memories"))
    semantic = _clean_lines(_object_value(memory, "semantic_memories"))
    procedural = _clean_lines(_object_value(memory, "procedural_memories"))
    legacy = _clean_lines(_object_value(memory, "legacy_summary"))
    counts = [len(episodic), len(semantic), len(procedural)]
    if any(counts):
        summary = f"三层记忆：E{counts[0]} / S{counts[1]} / P{counts[2]}"
        if legacy:
            summary += f"；旧版摘要：{legacy[0]}"
        return summary
    return ""


def _guided_answers_summary(guided_answers: Any) -> str:
    if guided_answers is None:
        return ""

    fields = [
        _normalize_text(_object_value(guided_answers, "most_common_topics")),
        _normalize_text(_object_value(guided_answers, "comfort_style")),
        _normalize_text(_object_value(guided_answers, "most_characteristic_event")),
        _normalize_text(_object_value(guided_answers, "repeated_phrases")),
        _normalize_text(_object_value(guided_answers, "care_habits")),
        _normalize_text(_object_value(guided_answers, "most_common_reminders")),
    ]
    filled = [item for item in fields if item]
    if not filled:
        return ""
    return f"引导补充：{len(filled)} 项 / {filled[0][:24]}"


def _reunion_layer_summary(memory: Any) -> str:
    if memory is None:
        return ""

    episodic = _clean_lines(_object_value(memory, "episodic_memories"))
    semantic = _clean_lines(_object_value(memory, "semantic_memories"))
    procedural = _clean_lines(_object_value(memory, "procedural_memories"))
    legacy = _clean_lines(_object_value(memory, "legacy_summary"))
    episodic_count = _normalize_text(_object_value(memory, "episodic_count"))
    semantic_count = _normalize_text(_object_value(memory, "semantic_count"))
    procedural_count = _normalize_text(_object_value(memory, "procedural_count"))
    if episodic or semantic or procedural or episodic_count or semantic_count or procedural_count:
        summary = f"三层记忆：E{episodic_count or len(episodic)} / S{semantic_count or len(semantic)} / P{procedural_count or len(procedural)}"
        if legacy:
            summary += f"；旧版摘要：{legacy[0]}"
        return summary
    return ""


def _reunion_guided_summary(guided_answers: Any) -> str:
    if guided_answers is None:
        return ""

    fields = [
        _normalize_text(_object_value(guided_answers, "recall_scenes")),
        _normalize_text(_object_value(guided_answers, "how_they_addressed_you")),
        _normalize_text(_object_value(guided_answers, "repeated_phrases")),
        _normalize_text(_object_value(guided_answers, "most_characteristic_moment")),
        _normalize_text(_object_value(guided_answers, "deepest_impression")),
        _normalize_text(_object_value(guided_answers, "care_style")),
        _normalize_text(_object_value(guided_answers, "typical_reminders")),
        _normalize_text(_object_value(guided_answers, "most_important_shared_memory")),
    ]
    filled = [item for item in fields if item]
    if not filled:
        return ""
    return f"引导补充：{len(filled)} 项 / {filled[0][:24]}"


def _reunion_policy_summary(policy: Any) -> str:
    if not isinstance(policy, dict):
        return ""

    parts: list[str] = []
    mode = _normalize_text(policy.get("mode"))
    if mode:
        parts.append(f"检索模式：{mode}")
    if policy.get("progressive_recall") is not None:
        parts.append(f"渐进式回忆：{'是' if policy.get('progressive_recall') else '否'}")
    recall_stage = _normalize_text(policy.get("recall_stage"))
    if recall_stage:
        parts.append(f"回忆档位：{recall_stage}")
    max_items = _normalize_text(policy.get("max_memory_items"))
    if max_items:
        parts.append(f"召回上限：{max_items}")
    priority_rules = _clean_lines(policy.get("priority_rules"))
    if priority_rules:
        parts.append("优先规则：" + " / ".join(priority_rules[:3]))
    fallback_rules = _clean_lines(policy.get("fallback_rules"))
    if fallback_rules:
        parts.append("降级规则：" + " / ".join(fallback_rules[:2]))
    return "；".join(parts[:4])


def _reunion_safety_summary(safety: Any) -> str:
    if not isinstance(safety, dict):
        return ""

    parts: list[str] = []
    protection = _clean_lines(safety.get("emotional_protection"))
    if protection:
        parts.append("情绪护栏：" + " / ".join(protection[:3]))
    boundaries = _clean_lines(safety.get("boundaries"))
    if boundaries:
        parts.append("边界：" + " / ".join(boundaries[:2]))
    toggles = []
    if safety.get("avoid_dependency_language"):
        toggles.append("避免依赖")
    if safety.get("avoid_claiming_certainty"):
        toggles.append("避免确定性")
    if safety.get("avoid_afterlife_claims"):
        toggles.append("避免超自然")
    if safety.get("de_escalate_distress"):
        toggles.append("高 distress 降温")
    if toggles:
        parts.append("护栏状态：" + " / ".join(toggles))
    return "；".join(parts[:4])


def _emotion_rules_summary(emotion_rules: Any) -> str:
    if not isinstance(emotion_rules, dict):
        return ""

    parts: list[str] = []
    summary = _normalize_text(emotion_rules.get("summary"))
    if summary:
        parts.append(summary)

    sequence = _clean_lines(emotion_rules.get("response_sequence"))
    if sequence:
        parts.append("回复顺序：" + " / ".join(sequence[:3]))

    priority = _clean_lines(emotion_rules.get("emotion_state_priority"))
    if priority:
        parts.append("情绪优先级：" + " / ".join(priority[:4]))

    boundary_rules = _clean_lines(emotion_rules.get("boundary_rules"))
    if boundary_rules:
        parts.append("边界规则：" + " / ".join(boundary_rules[:3]))

    return "；".join(parts[:4])


def _normalize_persona_type(value: Any) -> str:
    persona_type = _normalize_text(value) or "self_unified"
    if persona_type in _SELF_UNIFIED_ALIASES:
        return "self_unified"
    return persona_type


def _normalize_user_id(value: Any) -> int | None:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return None
    return normalized if normalized > 0 else None


def _build_slug(seed_name: str, persona_type: str) -> str:
    base = _normalize_text(seed_name).lower()
    base = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", base)
    base = re.sub(r"-+", "-", base).strip("-")
    if not base:
        base = "seed"
    kind = re.sub(r"[^a-z0-9]+", "-", persona_type.lower()).strip("-") or "persona"
    return f"my-{kind}-{base}-{uuid4().hex[:6]}"


def _build_summary(draft: CreateWizardDraft) -> str:
    if _normalize_text(draft.meta.create_type) == "self_unified":
        unified = draft.self_persona_unified or {}
        if isinstance(unified, dict):
            parts = []
            for key in ["work_system", "reply_persona", "thinking_dna", "memory_evidence", "reflection_rules"]:
                section = unified.get(key) or {}
                if isinstance(section, dict):
                    summary = _normalize_text(section.get("summary"))
                    if summary:
                        parts.append(summary)
            if parts:
                return " / ".join(parts)[:120]

    if _normalize_text(draft.meta.create_type) == "intimate_companion":
        profile = draft.relationship_profile or {}
        memory = draft.intimate_memory_base or {}
        understanding = getattr(draft, "intimate_understanding", None) or {}
        simulation = getattr(draft, "intimate_message_simulation", None) or {}
        maintenance = getattr(draft, "intimate_relationship_maintenance", None) or {}
        mirror = getattr(draft, "intimate_past_relationship", None) or {}
        raw_materials_summary = _material_summary_from_raw_materials(getattr(draft, "raw_materials", None))
        input_mode = _normalize_text(getattr(draft.meta, "input_mode", ""))
        mode_label = _INTIMATE_MODE_LABELS.get(input_mode, input_mode)
        profile_name = _normalize_text(
            profile.get("name") if isinstance(profile, dict) else getattr(profile, "name", "")
        )
        relationship_type = _normalize_text(
            profile.get("relationship_type") if isinstance(profile, dict) else getattr(profile, "relationship_type", "")
        )
        stage = _normalize_text(
            profile.get("relationship_stage") if isinstance(profile, dict) else getattr(profile, "relationship_stage", "")
        )
        tone = _normalize_text(profile.get("tone") if isinstance(profile, dict) else getattr(profile, "tone", ""))
        memories = []
        if isinstance(memory, dict):
            memories.extend(_clean_lines(memory.get("conversation_samples")))
            memories.extend(_clean_lines(memory.get("interaction_rules")))
            memories.extend(_clean_lines(memory.get("relationship_goals")))
            memories.extend(_clean_lines(memory.get("key_memories")))
            memories.extend(_clean_lines(memory.get("misunderstanding_points")))
            memories.extend(_clean_lines(memory.get("rewrite_targets")))
            memories.extend(_clean_lines(memory.get("interaction_patterns")))
            memories.extend(_clean_lines(memory.get("maintenance_goals")))
            memories.extend(_clean_lines(memory.get("relationship_memory")))
            memories.extend(_clean_lines(memory.get("expression_samples")))
        path_notes: list[str] = []
        if isinstance(understanding, dict):
            path_notes.extend(_clean_lines(understanding.get("misunderstanding_points")))
            path_notes.extend(_clean_lines(understanding.get("rewrite_targets")))
        if isinstance(simulation, dict):
            path_notes.extend(_clean_lines(simulation.get("reply_style_samples")))
            simulation_preferences = simulation.get("simulation_preferences")
            if isinstance(simulation_preferences, dict):
                tone = _normalize_text(simulation_preferences.get("tone"))
                candidate_count = _normalize_text(simulation_preferences.get("candidate_count"))
                if tone:
                    path_notes.append(f"语气偏好：{tone}")
                if candidate_count:
                    path_notes.append(f"候选数量：{candidate_count}")
        if isinstance(maintenance, dict):
            path_notes.extend(_clean_lines(maintenance.get("interaction_patterns")))
            path_notes.extend(_clean_lines(maintenance.get("maintenance_goals")))
        if isinstance(mirror, dict):
            path_notes.extend(_clean_lines(mirror.get("relationship_memory")))
            path_notes.extend(_clean_lines(mirror.get("expression_samples")))
        summary_parts = [part for part in [mode_label, profile_name, relationship_type, stage, tone] if part]
        if raw_materials_summary:
            summary_parts.append(raw_materials_summary)
        if summary_parts or memories or path_notes:
            combined = " · ".join(summary_parts)
            extras = path_notes or memories
            if extras:
                combined = f"{combined} / {extras[0]}" if combined else extras[0]
            return combined[:120]

    if _normalize_text(draft.meta.create_type) == "family_companion":
        profile = draft.persona_profile or {}
        memory = draft.memory_base or {}
        emotion_rules = getattr(draft, "emotion_rules", None)
        guided_answers = getattr(draft, "guided_memory_answers", None)
        raw_materials_summary = _material_summary_from_raw_materials(getattr(draft, "raw_materials", None))
        emotion_rules_summary = _emotion_rules_summary(emotion_rules)
        layer_summary = _family_memory_layer_summary(memory)
        guided_summary = _guided_answers_summary(guided_answers)
        family_subtype = _normalize_text(
            getattr(draft, "family_subtype", "") or getattr(draft.meta, "family_subtype", "")
        )
        family_subtype_label = _family_subtype_label(family_subtype)
        top_name = _normalize_text(getattr(draft.meta, "name", ""))
        profile_name = _normalize_text(profile.get("name") if isinstance(profile, dict) else getattr(profile, "name", ""))
        relationship_type = _normalize_text(
            profile.get("relationship_type") if isinstance(profile, dict) else getattr(profile, "relationship_type", "")
        )
        tone = _normalize_text(profile.get("tone") if isinstance(profile, dict) else getattr(profile, "tone", ""))
        memories = []
        if isinstance(memory, dict):
            memories.extend(_clean_lines(memory.get("chat_history_summary")))
            memories.extend(_clean_lines(memory.get("shared_events")))
            memories.extend(_clean_lines(memory.get("important_advice")))
            memories.extend(_clean_lines(memory.get("memory_fragments")))
            memories.extend(_clean_lines(memory.get("text_materials")))
            memories.extend(_clean_lines(memory.get("image_notes")))
            memories.extend(_clean_lines(memory.get("voice_notes")))
        if raw_materials_summary:
            summary_parts = [part for part in [top_name, family_subtype_label or relationship_type, raw_materials_summary] if part]
        else:
            summary_parts = [part for part in [top_name, family_subtype_label or relationship_type] if part]
        if guided_summary:
            summary_parts.append(guided_summary)
        if layer_summary:
            summary_parts.append(layer_summary)
        if emotion_rules_summary:
            summary_parts.append(emotion_rules_summary)
        if summary_parts or memories:
            combined = " · ".join(summary_parts)
            if memories:
                combined = f"{combined} / {memories[0]}" if combined else memories[0]
            return combined[:160]

    if _normalize_text(draft.meta.create_type) == "reunion_persona":
        profile = draft.reunion_persona_profile or {}
        memory = draft.reunion_memory_base or {}
        policy = draft.reunion_memory_retrieval_policy or {}
        safety = draft.reunion_safety_guardrails or {}
        guided_answers = getattr(draft, "reunion_guided_memory_answers", None)
        raw_materials_summary = _material_summary_from_raw_materials(getattr(draft, "raw_materials", None))
        profile_name = _normalize_text(profile.get("name") if isinstance(profile, dict) else getattr(profile, "name", ""))
        relationship_type = _normalize_text(
            profile.get("relationship_type") if isinstance(profile, dict) else getattr(profile, "relationship_type", "")
        )
        tone = _normalize_text(profile.get("tone") if isinstance(profile, dict) else getattr(profile, "tone", ""))
        retrieval_mode = _normalize_text(policy.get("mode") if isinstance(policy, dict) else getattr(policy, "mode", ""))
        memories = []
        if isinstance(memory, dict):
            memories.extend(_clean_lines(memory.get("chat_history_summary")))
            memories.extend(_clean_lines(memory.get("diary_notes")))
            memories.extend(_clean_lines(memory.get("letter_notes")))
            memories.extend(_clean_lines(memory.get("photo_notes")))
            memories.extend(_clean_lines(memory.get("voice_notes")))
            memories.extend(_clean_lines(memory.get("memory_fragments")))
            memories.extend(_clean_lines(memory.get("shared_memories")))
            memories.extend(_clean_lines(memory.get("episodic_memories")))
            memories.extend(_clean_lines(memory.get("semantic_memories")))
            memories.extend(_clean_lines(memory.get("procedural_memories")))
        layer_summary = _reunion_layer_summary(memory)
        guided_summary = _reunion_guided_summary(guided_answers)
        policy_summary = _reunion_policy_summary(policy)
        safety_summary = _reunion_safety_summary(safety)
        if guided_summary:
            summary_parts = [part for part in [profile_name, relationship_type, tone] if part]
        else:
            summary_parts = [part for part in [profile_name, relationship_type, tone] if part]
        if layer_summary:
            summary_parts.append(layer_summary)
        if guided_summary:
            summary_parts.append(guided_summary)
        if retrieval_mode:
            summary_parts.append(retrieval_mode)
        recall_stage = _normalize_text(_object_value(policy, "recall_stage"))
        if recall_stage:
            summary_parts.append(f"回忆档位：{recall_stage}")
        if policy_summary:
            summary_parts.append(policy_summary)
        if safety_summary:
            summary_parts.append(safety_summary)
        if raw_materials_summary:
            summary_parts.append(raw_materials_summary)
        if summary_parts or memories or safety_summary:
            combined = " · ".join(summary_parts)
            extras = memories
            if extras:
                combined = f"{combined} / {extras[0]}" if combined else extras[0]
            return combined[:160]

    pieces = [draft.profile, draft.mindset, draft.heuristics]
    for piece in pieces:
        text = _normalize_text(piece)
        if text:
            return text[:120]
    return ""


def _dump_draft(draft: CreateWizardDraft) -> str:
    return json.dumps(draft.model_dump(), ensure_ascii=False)


def _load_draft_payload(raw: str) -> CreateWizardDraft:
    payload = json.loads(raw or "{}")
    return CreateWizardDraft.model_validate(payload)


def _serialize_record(record: CreatedPersona) -> dict[str, Any]:
    draft = _load_draft_payload(record.draft_payload)
    material_summary = _material_summary_from_raw_materials(getattr(draft, "raw_materials", None))
    return {
        "id": record.id,
        "user_id": record.user_id,
        "slug": record.slug,
        "name": record.name,
        "persona_type": record.persona_type,
        "family_subtype": _normalize_text(getattr(draft, "family_subtype", "") or getattr(draft.meta, "family_subtype", "")),
        "summary": record.summary,
        "material_summary": material_summary,
        "status": record.status,
        "source_type": record.source_type,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "draft_payload": draft.model_dump(),
    }


def _serialize_summary(record: CreatedPersona) -> dict[str, Any]:
    draft = _load_draft_payload(record.draft_payload)
    material_summary = _material_summary_from_raw_materials(getattr(draft, "raw_materials", None))
    return {
        "id": record.id,
        "user_id": record.user_id,
        "slug": record.slug,
        "name": record.name,
        "persona_type": record.persona_type,
        "family_subtype": _normalize_text(getattr(draft, "family_subtype", "") or getattr(draft.meta, "family_subtype", "")),
        "summary": record.summary,
        "material_summary": material_summary,
        "status": record.status,
        "source_type": record.source_type,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def save_created_persona(
    db: Session,
    draft: CreateWizardDraft,
    *,
    record_id: int | None = None,
    source_type: str = "create_wizard",
    status: str = "saved",
    user_id: int | None = None,
) -> dict[str, Any]:
    normalized_source_type = _normalize_text(source_type) or "create_wizard"
    normalized_status = _normalize_text(status) or "saved"
    normalized_user_id = _normalize_user_id(user_id)
    persona_type = _normalize_persona_type(draft.meta.create_type)
    name = _normalize_text(draft.meta.name) or "未命名 Seed"
    summary = _build_summary(draft)
    stored_draft = CreateWizardDraft.model_validate(draft.model_dump())

    if record_id is not None:
        query = db.query(CreatedPersona).filter(CreatedPersona.id == record_id)
        if normalized_user_id is not None:
            query = query.filter(
                (CreatedPersona.user_id == normalized_user_id) | (CreatedPersona.user_id.is_(None))
            )
        record = query.first()
        if record is None:
            raise CreatedPersonaNotFoundError(f"Created persona not found: {record_id}")
        stored_draft.meta.slug = record.slug
        record.name = name
        record.persona_type = persona_type
        record.summary = summary
        record.draft_payload = _dump_draft(stored_draft)
        record.source_type = normalized_source_type
        record.status = normalized_status
        if normalized_user_id is not None:
            record.user_id = normalized_user_id
        db.flush()
        db.refresh(record)
        return _serialize_record(record)

    slug = _build_slug(name or draft.meta.slug or "seed", persona_type)
    stored_draft.meta.slug = slug
    record = CreatedPersona(
        user_id=normalized_user_id,
        slug=slug,
        name=name,
        persona_type=persona_type,
        summary=summary,
        draft_payload=_dump_draft(stored_draft),
        source_type=normalized_source_type,
        status=normalized_status,
    )
    db.add(record)
    db.flush()
    db.refresh(record)
    return _serialize_record(record)


def list_created_personas(db: Session, user_id: int | None = None) -> list[dict[str, Any]]:
    normalized_user_id = _normalize_user_id(user_id)
    if normalized_user_id is None:
        return []

    query = db.query(CreatedPersona)
    query = query.filter(CreatedPersona.user_id == normalized_user_id)
    records = query.order_by(CreatedPersona.updated_at.desc(), CreatedPersona.created_at.desc()).all()
    return [_serialize_summary(record) for record in records]


def get_created_persona(
    db: Session,
    record_id: int,
    user_id: int | None = None,
) -> dict[str, Any] | None:
    normalized_user_id = _normalize_user_id(user_id)
    if normalized_user_id is None:
        return None

    query = db.query(CreatedPersona).filter(CreatedPersona.id == record_id)
    query = query.filter(CreatedPersona.user_id == normalized_user_id)
    record = query.first()
    if record is None:
        return None
    return _serialize_record(record)


def get_created_persona_by_slug(db: Session, slug: str, user_id: int | None = None) -> dict[str, Any] | None:
    normalized_slug = _normalize_text(slug)
    if not normalized_slug:
        return None
    normalized_user_id = _normalize_user_id(user_id)
    if normalized_user_id is None:
        return None

    query = db.query(CreatedPersona).filter(CreatedPersona.slug == normalized_slug)
    query = query.filter(CreatedPersona.user_id == normalized_user_id)
    record = query.first()
    if record is None:
        return None
    return _serialize_record(record)


def load_created_persona_summary(
    db: Session,
    slug: str,
    user_id: int | None = None,
) -> dict[str, Any] | None:
    normalized_user_id = _normalize_user_id(user_id)
    if normalized_user_id is None:
        return None

    query = db.query(CreatedPersona).filter(CreatedPersona.slug == _normalize_text(slug))
    query = query.filter(CreatedPersona.user_id == normalized_user_id)
    record = query.first()
    if record is None:
        return None

    draft = _load_draft_payload(record.draft_payload)
    display_type = _PERSONA_TYPE_LABELS.get(record.persona_type, record.persona_type)
    intro = _normalize_text(getattr(draft.meta, "source_hint", ""))
    profile = _normalize_text(draft.profile)
    unified = getattr(draft, "self_persona_unified", None)
    if isinstance(unified, dict):
        profile = _normalize_text((unified.get("work_system") or {}).get("summary")) or profile
    relation_type = _normalize_text(getattr(draft, "relationship_type", ""))
    persona_profile = getattr(draft, "persona_profile", None)
    intimate_profile = getattr(draft, "relationship_profile", None)
    reunion_profile = getattr(draft, "reunion_persona_profile", None)
    if not relation_type and persona_profile is not None:
        if isinstance(persona_profile, dict):
            relation_type = _normalize_text(persona_profile.get("relationship_type"))
        else:
            relation_type = _normalize_text(getattr(persona_profile, "relationship_type", ""))
    if not relation_type and intimate_profile is not None:
        if isinstance(intimate_profile, dict):
            relation_type = _normalize_text(intimate_profile.get("relationship_type"))
        else:
            relation_type = _normalize_text(getattr(intimate_profile, "relationship_type", ""))
    if not relation_type and reunion_profile is not None:
        if isinstance(reunion_profile, dict):
            relation_type = _normalize_text(reunion_profile.get("relationship_type"))
        else:
            relation_type = _normalize_text(getattr(reunion_profile, "relationship_type", ""))

    return {
        "id": str(record.id),
        "slug": record.slug,
        "name": record.name,
        "category": display_type,
        "avatar": None,
        "intro": intro or (profile[:80] if profile else record.summary),
        "profile": draft.profile,
        "tags": [tag for tag in [display_type, relation_type] if tag],
        "topics": [],
        "recommendedQuestions": [],
        "version": getattr(draft.meta, "version", ""),
        "status": record.status,
        "isSeed": True,
        "seedSource": record.source_type,
        "seedGroup": display_type,
        "isFeatured": False,
        "isFavoritable": True,
        "personaKind": "created",
        "sortOrder": 999,
    }


def load_created_persona_skill(
    db: Session,
    slug: str,
    user_id: int | None = None,
) -> dict[str, Any] | None:
    normalized_user_id = _normalize_user_id(user_id)
    if normalized_user_id is None:
        return None

    query = db.query(CreatedPersona).filter(CreatedPersona.slug == _normalize_text(slug))
    query = query.filter(CreatedPersona.user_id == normalized_user_id)
    record = query.first()
    if record is None:
        return None
    draft = _load_draft_payload(record.draft_payload)
    return draft.model_dump()
