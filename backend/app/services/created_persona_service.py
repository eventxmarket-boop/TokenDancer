from __future__ import annotations

import json
import re
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.created_persona import CreatedPersona
from app.schemas.create_wizard import CreateWizardDraft


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


def _excerpt_text(value: Any, limit: int = 48) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    return text[:limit]


def _material_summary_from_raw_materials(raw_materials: Any) -> str:
    if not isinstance(raw_materials, dict):
        return ""

    parts: list[str] = []
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

    documents = _normalize_documents(raw_materials.get("uploaded_text_documents"))
    if documents:
        doc_items: list[str] = []
        for document in documents[:2]:
            filename = _normalize_text(document.get("filename"))
            content = _normalize_text(document.get("content"))
            snippet = content[:24]
            if filename and snippet:
                doc_items.append(f"{filename}：{snippet}")
            elif filename:
                doc_items.append(filename)
            elif snippet:
                doc_items.append(snippet)
        if doc_items:
            parts.append(f"文件材料：{' / '.join(doc_items)}")
        else:
            parts.append(f"文件材料：{len(documents)} 份")

    extra_notes = _excerpt_text(
        raw_materials.get("image_notes_text")
        or raw_materials.get("photo_notes_text")
        or raw_materials.get("voice_notes_text"),
        30,
    )
    if extra_notes:
        parts.append(f"备注：{extra_notes}")

    return "；".join(parts[:4])


def _normalize_persona_type(value: Any) -> str:
    persona_type = _normalize_text(value) or "self_unified"
    if persona_type in _SELF_UNIFIED_ALIASES:
        return "self_unified"
    return persona_type


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
            memories.extend(_clean_lines(memory.get("relationship_goals")))
        summary_parts = [part for part in [profile_name, relationship_type, stage, tone] if part]
        if summary_parts or memories:
            combined = " · ".join(summary_parts)
            if memories:
                combined = f"{combined} / {memories[0]}" if combined else memories[0]
            return combined[:120]

    if _normalize_text(draft.meta.create_type) == "family_companion":
        profile = draft.persona_profile or {}
        memory = draft.memory_base or {}
        raw_materials_summary = _material_summary_from_raw_materials(getattr(draft, "raw_materials", None))
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
        summary_parts = [part for part in [profile_name, relationship_type, tone] if part]
        if raw_materials_summary:
            summary_parts.append(raw_materials_summary)
        if summary_parts or memories:
            combined = " · ".join(summary_parts)
            if memories:
                combined = f"{combined} / {memories[0]}" if combined else memories[0]
            return combined[:120]

    if _normalize_text(draft.meta.create_type) == "reunion_persona":
        profile = draft.reunion_persona_profile or {}
        memory = draft.reunion_memory_base or {}
        policy = draft.reunion_memory_retrieval_policy or {}
        safety = draft.reunion_safety_guardrails or {}
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
        safety_notes = []
        if isinstance(safety, dict):
            safety_notes.extend(_clean_lines(safety.get("boundaries")))
            safety_notes.extend(_clean_lines(safety.get("emotional_protection")))
        summary_parts = [part for part in [profile_name, relationship_type, tone, retrieval_mode] if part]
        if raw_materials_summary:
            summary_parts.append(raw_materials_summary)
        if summary_parts or memories or safety_notes:
            combined = " · ".join(summary_parts)
            extras = memories or safety_notes
            if extras:
                combined = f"{combined} / {extras[0]}" if combined else extras[0]
            return combined[:120]

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
    return {
        "id": record.id,
        "slug": record.slug,
        "name": record.name,
        "persona_type": record.persona_type,
        "summary": record.summary,
        "status": record.status,
        "source_type": record.source_type,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "draft_payload": draft.model_dump(),
    }


def _serialize_summary(record: CreatedPersona) -> dict[str, Any]:
    return {
        "id": record.id,
        "slug": record.slug,
        "name": record.name,
        "persona_type": record.persona_type,
        "summary": record.summary,
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
) -> dict[str, Any]:
    normalized_source_type = _normalize_text(source_type) or "create_wizard"
    normalized_status = _normalize_text(status) or "saved"
    persona_type = _normalize_persona_type(draft.meta.create_type)
    name = _normalize_text(draft.meta.name) or "未命名 Seed"
    summary = _build_summary(draft)
    stored_draft = CreateWizardDraft.model_validate(draft.model_dump())

    if record_id is not None:
        record = db.query(CreatedPersona).filter(CreatedPersona.id == record_id).first()
        if record is None:
            raise CreatedPersonaNotFoundError(f"Created persona not found: {record_id}")
        stored_draft.meta.slug = record.slug
        record.name = name
        record.persona_type = persona_type
        record.summary = summary
        record.draft_payload = _dump_draft(stored_draft)
        record.source_type = normalized_source_type
        record.status = normalized_status
        db.flush()
        db.refresh(record)
        return _serialize_record(record)

    slug = _build_slug(name or draft.meta.slug or "seed", persona_type)
    stored_draft.meta.slug = slug
    record = CreatedPersona(
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


def list_created_personas(db: Session) -> list[dict[str, Any]]:
    records = (
        db.query(CreatedPersona)
        .order_by(CreatedPersona.updated_at.desc(), CreatedPersona.created_at.desc())
        .all()
    )
    return [_serialize_summary(record) for record in records]


def get_created_persona(db: Session, record_id: int) -> dict[str, Any] | None:
    record = db.query(CreatedPersona).filter(CreatedPersona.id == record_id).first()
    if record is None:
        return None
    return _serialize_record(record)


def get_created_persona_by_slug(db: Session, slug: str) -> dict[str, Any] | None:
    normalized_slug = _normalize_text(slug)
    if not normalized_slug:
        return None
    record = db.query(CreatedPersona).filter(CreatedPersona.slug == normalized_slug).first()
    if record is None:
        return None
    return _serialize_record(record)


def load_created_persona_summary(db: Session, slug: str) -> dict[str, Any] | None:
    record = db.query(CreatedPersona).filter(CreatedPersona.slug == _normalize_text(slug)).first()
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


def load_created_persona_skill(db: Session, slug: str) -> dict[str, Any] | None:
    record = db.query(CreatedPersona).filter(CreatedPersona.slug == _normalize_text(slug)).first()
    if record is None:
        return None
    draft = _load_draft_payload(record.draft_payload)
    return draft.model_dump()
