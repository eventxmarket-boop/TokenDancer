from __future__ import annotations

import re
from datetime import datetime
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.base_mixins import utcnow
from app.services.llm_gateway import generate_reply
from app.services.persona_loader import load_persona_skill, load_persona_summary
from app.services.prompt_builder import build_chat_messages


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


def _get_or_create_session(db: Session, persona_slug: str, session_id: str | None) -> ChatSession:
    normalized_session_id = (session_id or "").strip()
    session: ChatSession | None = None

    if normalized_session_id:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.session_id == normalized_session_id)
            .first()
        )

    if session is not None:
        if session.persona_slug != persona_slug:
            normalized_session_id = uuid4().hex
            session = ChatSession(session_id=normalized_session_id, persona_slug=persona_slug)
            db.add(session)
            db.flush()
            return session

        session.persona_slug = persona_slug
        session.updated_at = utcnow()
        db.flush()
        return session

    if not normalized_session_id:
        normalized_session_id = uuid4().hex

    session = ChatSession(session_id=normalized_session_id, persona_slug=persona_slug)
    db.add(session)
    db.flush()
    return session


def _load_recent_history(db: Session, session_id: str, limit: int = 12) -> list[dict[str, str]]:
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .all()
    )
    recent_rows = rows[-limit:] if limit > 0 else rows
    return [{"role": row.role, "content": row.content} for row in recent_rows]


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


def get_chat_session_detail(db: Session, session_id: str) -> dict[str, object] | None:
    normalized_session_id = session_id.strip()
    if not normalized_session_id:
        raise ChatServiceError("session_id 不能为空")

    session = (
        db.query(ChatSession)
        .filter(ChatSession.session_id == normalized_session_id)
        .first()
    )
    if session is None:
        return None

    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == normalized_session_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .all()
    )
    persona_summary = load_persona_summary(session.persona_slug) or {}
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


def get_latest_chat_session_for_persona(db: Session, persona_slug: str) -> dict[str, object] | None:
    normalized_slug = persona_slug.strip()
    if not normalized_slug:
        raise ChatServiceError("persona_slug 不能为空")

    session = (
        db.query(ChatSession)
        .filter(ChatSession.persona_slug == normalized_slug)
        .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        .first()
    )
    if session is None:
        return None
    return get_chat_session_detail(db, session.session_id)


def get_recent_chat_sessions(db: Session, limit: int = 10) -> list[dict[str, object]]:
    normalized_limit = max(1, min(int(limit or 10), 50))
    sessions = (
        db.query(ChatSession)
        .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        .limit(normalized_limit)
        .all()
    )

    summaries: list[dict[str, object]] = []
    for session in sessions:
        has_messages = (
            db.query(ChatMessage.id)
            .filter(ChatMessage.session_id == session.session_id)
            .first()
        )
        if has_messages is None:
            continue

        persona_summary = load_persona_summary(session.persona_slug) or {}
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
) -> dict[str, object]:
    persona = load_persona_skill(persona_slug)
    if persona is None:
        raise PersonaNotFoundError(f"Persona not found: {persona_slug}")

    persona_meta = persona.get("meta") or {}
    persona_name = str(persona_meta.get("name") or persona_slug).strip()

    normalized_message = user_message.strip()
    if not normalized_message:
        raise ChatServiceError("消息内容不能为空")

    session = _get_or_create_session(db, persona_slug, session_id)
    history = _load_recent_history(db, session.session_id, limit=12)
    if not (session.title or "").strip():
        first_user_message = next(
            (message["content"] for message in history if message.get("role") == "user" and str(message.get("content", "")).strip()),
            normalized_message,
        )
        session.title = _build_session_title(persona_name, first_user_message)
    messages = build_chat_messages(persona, history, normalized_message)

    try:
        reply = await generate_reply(messages, db=db)
        _persist_messages(db, session.session_id, normalized_message, reply)
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


def clear_chat_session(db: Session, session_id: str) -> str:
    normalized_session_id = session_id.strip()
    if not normalized_session_id:
        raise ChatServiceError("session_id 不能为空")

    session = (
        db.query(ChatSession)
        .filter(ChatSession.session_id == normalized_session_id)
        .first()
    )
    if session is None:
        raise ChatServiceError(f"session not found: {normalized_session_id}")

    new_session_id = uuid4().hex
    new_session = ChatSession(session_id=new_session_id, persona_slug=session.persona_slug)
    db.add(new_session)
    db.commit()
    return new_session_id
