from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.services.llm_gateway import generate_reply
from app.services.persona_loader import load_persona_skill
from app.services.prompt_builder import build_chat_messages
from app.models.base_mixins import utcnow


class ChatServiceError(RuntimeError):
    pass


class PersonaNotFoundError(ChatServiceError):
    pass


@dataclass(slots=True)
class ChatResult:
    session_id: str
    persona_slug: str
    reply: str
    model: str
    usage: dict[str, int]
    latency_ms: int

    def as_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "persona_slug": self.persona_slug,
            "reply": self.reply,
            "model": self.model,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
        }


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

    normalized_message = user_message.strip()
    if not normalized_message:
        raise ChatServiceError("消息内容不能为空")

    session = _get_or_create_session(db, persona_slug, session_id)
    history = _load_recent_history(db, session.session_id, limit=12)
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
        reply=str(reply.get("content", "")).strip(),
        model=str(reply.get("model", "")).strip(),
        usage=reply.get("usage", {}) if isinstance(reply.get("usage", {}), dict) else {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
        latency_ms=int(reply.get("latency_ms") or 0),
    ).as_dict()


def clear_chat_session(db: Session, session_id: str) -> None:
    normalized_session_id = session_id.strip()
    if not normalized_session_id:
        raise ChatServiceError("session_id 不能为空")

    (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == normalized_session_id)
        .delete(synchronize_session=False)
    )
    session = (
        db.query(ChatSession)
        .filter(ChatSession.session_id == normalized_session_id)
        .first()
    )
    if session is not None:
        session.updated_at = utcnow()
    db.commit()
