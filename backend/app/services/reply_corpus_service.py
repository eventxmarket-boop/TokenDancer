from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.reply_corpus import ReplyCorpus
from app.schemas.reply_corpus import ReplyCorpusPublic, ReplyCorpusUpsertRequest

DEFAULT_REPLY_CORPUS_TYPE = "高情商回复"
DEFAULT_REPLY_CORPUS_TITLE = "高情商回复"


class ReplyCorpusServiceError(RuntimeError):
    pass


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _serialize(corpus: ReplyCorpus) -> ReplyCorpusPublic:
    return ReplyCorpusPublic(
        id=corpus.id,
        title=corpus.title,
        corpus_type=corpus.corpus_type,
        content=corpus.content,
        sort_order=corpus.sort_order,
        is_enabled=corpus.is_enabled,
        created_at=corpus.created_at,
        updated_at=corpus.updated_at,
    )


def _ordered_corpora(db: Session) -> list[ReplyCorpus]:
    return (
        db.query(ReplyCorpus)
        .order_by(
            ReplyCorpus.is_enabled.desc(),
            ReplyCorpus.sort_order.desc(),
            ReplyCorpus.updated_at.desc(),
            ReplyCorpus.id.desc(),
        )
        .all()
    )


def list_reply_corpora(db: Session) -> list[ReplyCorpusPublic]:
    return [_serialize(corpus) for corpus in _ordered_corpora(db)]


def get_reply_corpus_dashboard(db: Session) -> dict[str, Any]:
    return {"items": list_reply_corpora(db)}


def _apply_payload(corpus: ReplyCorpus, payload: ReplyCorpusUpsertRequest) -> ReplyCorpus:
    title = _normalize_text(payload.title)
    corpus_type = _normalize_text(payload.corpus_type) or DEFAULT_REPLY_CORPUS_TYPE
    content = _normalize_text(payload.content)
    if not content:
        raise ReplyCorpusServiceError("语料内容不能为空")

    corpus.title = title or corpus_type or DEFAULT_REPLY_CORPUS_TITLE
    corpus.corpus_type = corpus_type
    corpus.content = content
    corpus.sort_order = int(payload.sort_order or 0)
    corpus.is_enabled = bool(payload.is_enabled)
    return corpus


def save_reply_corpus(db: Session, payload: ReplyCorpusUpsertRequest) -> ReplyCorpusPublic:
    target: ReplyCorpus | None = None
    if payload.id is not None:
        target = db.query(ReplyCorpus).filter(ReplyCorpus.id == payload.id).first()
        if target is None:
            raise ReplyCorpusServiceError(f"未找到回复语料: {payload.id}")

    if target is None:
        target = ReplyCorpus()
        db.add(target)

    target = _apply_payload(target, payload)
    db.commit()
    db.refresh(target)
    return _serialize(target)


def update_reply_corpus(db: Session, corpus_id: int, payload: ReplyCorpusUpsertRequest) -> ReplyCorpusPublic:
    target = db.query(ReplyCorpus).filter(ReplyCorpus.id == corpus_id).first()
    if target is None:
        raise ReplyCorpusServiceError(f"未找到回复语料: {corpus_id}")

    target = _apply_payload(target, payload)
    db.commit()
    db.refresh(target)
    return _serialize(target)


def delete_reply_corpus(db: Session, corpus_id: int) -> ReplyCorpusPublic:
    target = db.query(ReplyCorpus).filter(ReplyCorpus.id == corpus_id).first()
    if target is None:
        raise ReplyCorpusServiceError(f"未找到回复语料: {corpus_id}")

    serialized = _serialize(target)
    db.delete(target)
    db.commit()
    return serialized


def _truncate_block(text: str, max_chars: int = 1200) -> str:
    cleaned = _normalize_text(text)
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip("，,。！？!?；; ") + "…"


def build_reply_corpus_context(db: Session | None = None) -> str:
    if db is None:
        return ""

    corpora = [corpus for corpus in _ordered_corpora(db) if corpus.is_enabled and _normalize_text(corpus.content)]
    if not corpora:
        return ""

    sections: list[str] = []
    for corpus in corpora[:6]:
        title = _normalize_text(corpus.title) or _normalize_text(corpus.corpus_type) or DEFAULT_REPLY_CORPUS_TITLE
        corpus_type = _normalize_text(corpus.corpus_type) or DEFAULT_REPLY_CORPUS_TYPE
        content = _truncate_block(corpus.content, 700)
        sections.append(f"【{corpus_type}】{title}\n{content}")

    combined = "\n\n".join(sections).strip()
    return _truncate_block(combined, 3200)
