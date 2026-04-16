from __future__ import annotations

import re
from datetime import datetime
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.base_mixins import utcnow
from app.services.chat_summary_service import (
    generate_session_summary,
    retrieve_relevant_older_messages,
    should_refresh_summary,
)
from app.services.created_persona_service import (
    load_created_persona_skill,
    load_created_persona_summary,
)
from app.services.llm_gateway import generate_reply
from app.services.persona_loader import load_persona_skill, load_persona_summary
from app.services.prompt_builder import build_chat_messages
from app.services.family_companion_service import build_family_companion_context
from app.services.intimate_companion_service import build_intimate_companion_context
from app.services.intimate_understanding_service import build_intimate_understanding_context
from app.services.message_simulation_service import build_message_simulation_context
from app.services.relationship_maintenance_service import build_relationship_maintenance_context
from app.services.past_relationship_service import build_past_relationship_context
from app.services.reunion_persona_service import build_reunion_persona_context
from app.services.zhangxuefeng_research import (
    classify_zhangxuefeng_question,
    research_education_question,
)


CONTEXT_HISTORY_LIMIT = 20
SUMMARY_REFRESH_BATCH = 8


class ChatServiceError(RuntimeError):
    pass


class PersonaNotFoundError(ChatServiceError):
    pass


@dataclass(slots=True)
class ChatResult:
    session_id: str
    persona_slug: str
    title: str
    reply: str
    model: str
    usage: dict[str, int]
    latency_ms: int

    def as_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "persona_slug": self.persona_slug,
            "title": self.title,
            "reply": self.reply,
            "model": self.model,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
        }


@dataclass(slots=True)
class ChatMessageRecord:
    role: str
    content: str
    model: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    created_at: datetime

    def as_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "content": self.content,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class RecentSessionRecord:
    id: str
    persona_slug: str
    persona_name: str
    title: str
    updated_at: datetime

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "persona_slug": self.persona_slug,
            "persona_name": self.persona_name,
            "title": self.title,
            "updated_at": self.updated_at,
        }


def _build_session_title(persona_name: str, source_text: str) -> str:
    cleaned = re.sub(r"\s+", " ", source_text or "").strip()
    cleaned = cleaned.strip("。！？!?.,，；;：:、/\\|·`~\"' ")

    fallback = f"{persona_name}对话" if persona_name.strip() else "新会话"
    if not cleaned:
        return fallback

    title = cleaned[:18]
    if len(cleaned) > 18:
        title = title.rstrip("。！？!?.,，；;：:、/\\|·`~\"' ") + "…"

    return title if len(title) >= 4 else fallback


def _resolve_session_title(
    session: ChatSession,
    *,
    persona_name: str | None = None,
    first_user_message: str | None = None,
) -> str:
    title = (session.title or "").strip()
    if title:
        return title

    return _build_session_title(
        persona_name or session.persona_slug,
        first_user_message or "",
    )


def _load_persona_summary_any(db: Session, slug: str, user_id: int | None = None) -> dict[str, object] | None:
    summary = load_persona_summary(slug)
    if summary is not None:
        return summary
    return load_created_persona_summary(db, slug, user_id=user_id)


def _load_persona_skill_any(db: Session, slug: str, user_id: int | None = None) -> dict[str, object] | None:
    skill = load_persona_skill(slug)
    if skill is not None:
        return skill
    return load_created_persona_skill(db, slug, user_id=user_id)


def _get_or_create_session(
    db: Session,
    persona_slug: str,
    session_id: str | None,
    user_id: int | None = None,
) -> ChatSession:
    normalized_session_id = (session_id or "").strip()
    session: ChatSession | None = None

    if normalized_session_id:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.session_id == normalized_session_id)
            .first()
        )
        if session is not None:
            normalized_user_id = user_id if user_id and user_id > 0 else None
            if normalized_user_id is None:
                if session.user_id is not None:
                    session = None
            elif session.user_id != normalized_user_id:
                session = None

    if session is not None:
        if session.persona_slug != persona_slug:
            normalized_session_id = uuid4().hex
            session = ChatSession(
                session_id=normalized_session_id,
                persona_slug=persona_slug,
                user_id=user_id if user_id and user_id > 0 else None,
            )
            db.add(session)
            db.flush()
            return session

        session.persona_slug = persona_slug
        if user_id and user_id > 0:
            session.user_id = user_id
        session.updated_at = utcnow()
        db.flush()
        return session

    if not normalized_session_id:
        normalized_session_id = uuid4().hex

    session = ChatSession(
        session_id=normalized_session_id,
        persona_slug=persona_slug,
        user_id=user_id if user_id and user_id > 0 else None,
    )
    db.add(session)
    db.flush()
    return session


def _load_session_history(db: Session, session_id: str) -> list[dict[str, str]]:
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .all()
    )
    return [{"role": row.role, "content": row.content} for row in rows]


def _load_recent_history(db: Session, session_id: str, limit: int = CONTEXT_HISTORY_LIMIT) -> list[dict[str, str]]:
    history = _load_session_history(db, session_id)
    return history[-limit:] if limit > 0 else history


def _count_messages_since_summary(db: Session, session: ChatSession) -> int:
    if not session.summary_updated_at:
        return (
            db.query(ChatMessage.id)
            .filter(ChatMessage.session_id == session.session_id)
            .count()
        )

    return (
        db.query(ChatMessage.id)
        .filter(
            ChatMessage.session_id == session.session_id,
            ChatMessage.created_at > session.summary_updated_at,
        )
        .count()
    )


def _sync_session_summary(db: Session, session: ChatSession, history: list[dict[str, str]]) -> str | None:
    summary_text = (session.summary_text or "").strip() or None
    message_count = len(history)
    messages_since_summary = _count_messages_since_summary(db, session)
    should_refresh = should_refresh_summary(
        message_count,
        session.summary_updated_at,
        messages_since_summary,
    )

    if summary_text and not should_refresh:
        return summary_text

    if not summary_text and message_count <= CONTEXT_HISTORY_LIMIT:
        return None

    older_messages = history[:-CONTEXT_HISTORY_LIMIT] if message_count > CONTEXT_HISTORY_LIMIT else history
    if not older_messages and not summary_text:
        return None

    refreshed = generate_session_summary(older_messages, previous_summary=summary_text)
    refreshed = (refreshed or "").strip()
    if not refreshed:
        return summary_text

    session.summary_text = refreshed
    session.summary_updated_at = utcnow()
    db.flush()
    return refreshed


def build_context_for_chat(db: Session, session: ChatSession) -> tuple[str | None, list[dict[str, str]]]:
    history = _load_session_history(db, session.session_id)
    summary_text = _sync_session_summary(db, session, history)
    recent_history = history[-CONTEXT_HISTORY_LIMIT:] if CONTEXT_HISTORY_LIMIT > 0 else history
    return summary_text, recent_history


def summarize_older_messages(messages: list[dict[str, str]]) -> str | None:
    # Reserved for a future retrieval layer; the current release still relies on rolling summary + recent turns.
    if not messages:
        return None
    return None


def build_context_messages(
    persona: dict[str, object],
    history: list[dict[str, str]],
    user_message: str,
    *,
    session_summary: str | None = None,
    facts_context: str | None = None,
    aux_context: str | None = None,
) -> list[dict[str, str]]:
    recent_history = history[-CONTEXT_HISTORY_LIMIT:] if CONTEXT_HISTORY_LIMIT > 0 else history
    _ = summarize_older_messages(history[:-CONTEXT_HISTORY_LIMIT]) if len(history) > CONTEXT_HISTORY_LIMIT else None
    return build_chat_messages(
        persona,
        recent_history,
        user_message,
        session_summary=session_summary,
        facts_context=facts_context,
        aux_context=aux_context,
    )


def _format_research_context(research: dict[str, object]) -> str:
    summary_lines = [
        str(line).strip()
        for line in (research.get("facts_summary") or [])
        if str(line).strip()
    ]
    sources_hint = [
        str(line).strip()
        for line in (research.get("sources_hint") or [])
        if str(line).strip()
    ]
    question_class = str(research.get("question_class") or "").strip()
    parts: list[str] = []
    if question_class:
        parts.append(f"问题分类：{question_class}")
    if summary_lines:
        parts.append("核实清单：")
        parts.extend(f"- {line}" for line in summary_lines)
    if sources_hint:
        parts.append("优先核实来源：")
        parts.extend(f"- {line}" for line in sources_hint)
    return "\n".join(parts).strip()


def _serialize_message(row: ChatMessage) -> dict[str, object]:
    return ChatMessageRecord(
        role=row.role,
        content=row.content,
        model=row.model,
        prompt_tokens=int(row.prompt_tokens or 0),
        completion_tokens=int(row.completion_tokens or 0),
        total_tokens=int(row.total_tokens or 0),
        latency_ms=int(row.latency_ms or 0),
        created_at=row.created_at,
    ).as_dict()


def get_chat_session_detail(db: Session, session_id: str, user_id: int | None = None) -> dict[str, object] | None:
    normalized_session_id = session_id.strip()
    if not normalized_session_id:
        raise ChatServiceError("session_id 不能为空")

    query = db.query(ChatSession).filter(ChatSession.session_id == normalized_session_id)
    if user_id and user_id > 0:
        query = query.filter(ChatSession.user_id == user_id)
    else:
        query = query.filter(ChatSession.user_id.is_(None))

    session = query.first()
    if session is None:
        return None

    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == normalized_session_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .all()
    )
    persona_summary = _load_persona_summary_any(db, session.persona_slug, user_id=user_id) or {}
    persona_name = str(persona_summary.get("name") or session.persona_slug).strip()
    first_user_message = next(
        (row.content for row in rows if row.role == "user" and row.content.strip()),
        "",
    )
    return {
        "session_id": session.session_id,
        "persona_slug": session.persona_slug,
        "title": _resolve_session_title(
            session,
            persona_name=persona_name,
            first_user_message=first_user_message,
        ),
        "messages": [_serialize_message(row) for row in rows],
    }


def get_latest_chat_session_for_persona(
    db: Session,
    persona_slug: str,
    user_id: int | None = None,
) -> dict[str, object] | None:
    normalized_slug = persona_slug.strip()
    if not normalized_slug:
        raise ChatServiceError("persona_slug 不能为空")

    query = db.query(ChatSession).filter(ChatSession.persona_slug == normalized_slug)
    if user_id and user_id > 0:
        query = query.filter(ChatSession.user_id == user_id)
    else:
        query = query.filter(ChatSession.user_id.is_(None))

    session = query.order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc()).first()
    if session is None:
        return None
    return get_chat_session_detail(db, session.session_id, user_id=user_id)


def get_recent_chat_sessions(db: Session, limit: int = 10, user_id: int | None = None) -> list[dict[str, object]]:
    normalized_limit = max(1, min(int(limit or 10), 50))
    query = db.query(ChatSession)
    if user_id and user_id > 0:
        query = query.filter(ChatSession.user_id == user_id)
    else:
        query = query.filter(ChatSession.user_id.is_(None))
    sessions = query.order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc()).limit(normalized_limit).all()

    summaries: list[dict[str, object]] = []
    for session in sessions:
        has_messages = (
            db.query(ChatMessage.id)
            .filter(ChatMessage.session_id == session.session_id)
            .first()
        )
        if has_messages is None:
            continue

        persona_summary = _load_persona_summary_any(db, session.persona_slug, user_id=user_id) or {}
        persona_name = str(persona_summary.get("name") or session.persona_slug).strip()
        first_user = (
            db.query(ChatMessage.content)
            .filter(
                ChatMessage.session_id == session.session_id,
                ChatMessage.role == "user",
            )
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
            .first()
        )
        first_user_message = str(first_user[0]).strip() if first_user and first_user[0] else ""
        summaries.append(
            RecentSessionRecord(
                id=session.session_id,
                persona_slug=session.persona_slug,
                persona_name=persona_name,
                title=_resolve_session_title(
                    session,
                    persona_name=persona_name,
                    first_user_message=first_user_message,
                ),
                updated_at=session.updated_at,
            ).as_dict()
        )

    return summaries


def _persist_messages(
    db: Session,
    session_id: str,
    user_message: str,
    reply: dict[str, object],
) -> None:
    usage = reply.get("usage") if isinstance(reply, dict) else {}
    if not isinstance(usage, dict):
        usage = {}

    user_row = ChatMessage(
        session_id=session_id,
        role="user",
        content=user_message,
        model=None,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        latency_ms=0,
    )
    assistant_row = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=str(reply.get("content", "")).strip(),
        model=str(reply.get("model", "")).strip() or None,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        total_tokens=int(usage.get("total_tokens") or 0),
        latency_ms=int(reply.get("latency_ms") or 0),
    )
    db.add(user_row)
    db.add(assistant_row)


async def chat_with_persona(
    persona_slug: str,
    session_id: str | None,
    user_message: str,
    db: Session,
    user_id: int | None = None,
) -> dict[str, object]:
    persona = _load_persona_skill_any(db, persona_slug, user_id=user_id)
    if persona is None:
        raise PersonaNotFoundError(f"Persona not found: {persona_slug}")

    persona_meta = persona.get("meta") or {}
    persona_name = str(persona_meta.get("name") or persona_slug).strip()
    create_type = str(persona_meta.get("create_type") or "").strip()
    is_family_companion = create_type == "family_companion"
    if not is_family_companion:
        family_source_repo = str(persona_meta.get("source_repo") or "").strip()
        is_family_companion = family_source_repo in {"parents-skills+MamaSkill", "parents-skills", "MamaSkill"}
    is_reunion_persona = create_type == "reunion_persona"
    if not is_reunion_persona:
        reunion_source_repo = str(persona_meta.get("source_repo") or "").strip()
        is_reunion_persona = reunion_source_repo == "reunion-skill"
    is_intimate_companion = create_type == "intimate_companion"
    if not is_intimate_companion:
        intimate_source_repo = str(persona_meta.get("source_repo") or "").strip()
        is_intimate_companion = intimate_source_repo in {
            "relationship-training-skill+xinyi",
            "crush-skill",
            "partner-skill+npy-skill",
            "ex-skill+first-love-skill+shuixian-skill",
        }

    normalized_message = user_message.strip()
    if not normalized_message:
        raise ChatServiceError("消息内容不能为空")

    session = _get_or_create_session(db, persona_slug, session_id, user_id=user_id)
    session_summary, history = build_context_for_chat(db, session)
    if not (session.title or "").strip():
        first_user_message = next(
            (
                message["content"]
                for message in history
                if message.get("role") == "user" and str(message.get("content", "")).strip()
            ),
            normalized_message,
        )
        session.title = _build_session_title(persona_name, first_user_message)

    facts_context: str | None = None
    aux_context: str | None = None
    if persona_slug.strip() == "zhang_xue_feng":
        question_class = classify_zhangxuefeng_question(normalized_message, history)
        if question_class in {"fact_required", "hybrid"}:
            research = await research_education_question(normalized_message, classification=question_class)
            facts_context = _format_research_context(research)
    elif is_family_companion:
        aux_context = build_family_companion_context(persona, history, normalized_message)
    elif is_reunion_persona:
        aux_context = build_reunion_persona_context(persona, history, normalized_message)
    elif is_intimate_companion:
        intimate_mode = str(persona_meta.get("input_mode") or "").strip()
        if intimate_mode == "relationship_understanding":
            aux_context = build_intimate_understanding_context(persona, history, normalized_message)
        elif intimate_mode == "message_simulation":
            aux_context = build_message_simulation_context(persona, history, normalized_message)
        elif intimate_mode == "partner_maintenance":
            aux_context = build_relationship_maintenance_context(persona, history, normalized_message)
        elif intimate_mode == "past_relation_mirror":
            aux_context = build_past_relationship_context(persona, history, normalized_message)
        else:
            aux_context = build_intimate_companion_context(persona, history, normalized_message)

    messages = build_context_messages(
        persona,
        history,
        normalized_message,
        session_summary=session_summary,
        facts_context=facts_context,
        aux_context=aux_context,
    )

    try:
        reply = await generate_reply(messages, db=db)
        _persist_messages(db, session.session_id, normalized_message, reply)
        db.flush()
        refreshed_history = _load_session_history(db, session.session_id)
        if should_refresh_summary(
            len(refreshed_history),
            session.summary_updated_at,
            _count_messages_since_summary(db, session),
        ):
            refreshed_summary = generate_session_summary(
                refreshed_history[:-CONTEXT_HISTORY_LIMIT] if len(refreshed_history) > CONTEXT_HISTORY_LIMIT else refreshed_history,
                previous_summary=session.summary_text,
            )
            refreshed_summary = (refreshed_summary or "").strip()
            if refreshed_summary:
                session.summary_text = refreshed_summary
                session.summary_updated_at = utcnow()
        session.updated_at = utcnow()
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ChatResult(
        session_id=session.session_id,
        persona_slug=persona_slug,
        title=(session.title or "").strip(),
        reply=str(reply.get("content", "")).strip(),
        model=str(reply.get("model", "")).strip(),
        usage=reply.get("usage", {}) if isinstance(reply.get("usage", {}), dict) else {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
        latency_ms=int(reply.get("latency_ms") or 0),
    ).as_dict()


def clear_chat_session(db: Session, session_id: str, user_id: int | None = None) -> str:
    normalized_session_id = session_id.strip()
    if not normalized_session_id:
        raise ChatServiceError("session_id 不能为空")

    query = db.query(ChatSession).filter(ChatSession.session_id == normalized_session_id)
    if user_id and user_id > 0:
        query = query.filter(ChatSession.user_id == user_id)
    else:
        query = query.filter(ChatSession.user_id.is_(None))

    session = query.first()
    if session is None:
        raise ChatServiceError(f"session not found: {normalized_session_id}")

    new_session_id = uuid4().hex
    new_session = ChatSession(
        session_id=new_session_id,
        persona_slug=session.persona_slug,
        user_id=session.user_id if session.user_id is not None else (user_id if user_id and user_id > 0 else None),
    )
    db.add(new_session)
    db.commit()
    return new_session_id
