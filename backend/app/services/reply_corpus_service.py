from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.reply_corpus import ReplyCorpus
from app.schemas.reply_corpus import ReplyCorpusPublic, ReplyCorpusUpsertRequest

DEFAULT_REPLY_CORPUS_TYPE = "高情商回复"
DEFAULT_REPLY_CORPUS_TITLE = "高情商回复"
DEFAULT_SCOPE_LABEL = "通用"

TARGET_PERSON_LABELS: dict[str, str] = {
    "any": "通用",
    "crush": "暧昧对象",
    "partner": "伴侣",
    "ex": "前任",
    "colleague": "同事",
    "boss": "上司 / 领导",
    "client": "客户 / 对接方",
    "public_sector": "体制内 / 公务沟通",
    "mentor": "导师 / 前辈",
    "friend": "朋友",
    "family": "家人",
}

SCENE_LABELS: dict[str, str] = {
    "any": "通用",
    "daily": "日常聊天",
    "conflict": "冷战 / 冲突",
    "push_forward": "推进关系",
    "work_report": "工作汇报",
    "follow_up": "跟进未回复",
    "formal_notice": "正式通知",
    "rejection": "拒绝 / 婉拒",
    "repair": "解释误会 / 修复",
}


class ReplyCorpusServiceError(RuntimeError):
    pass


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _serialize(corpus: ReplyCorpus) -> ReplyCorpusPublic:
    return ReplyCorpusPublic(
        id=corpus.id,
        title=corpus.title,
        target_person_type=corpus.target_person_type,
        scene_type=corpus.scene_type,
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
    target_person_type = _normalize_text(payload.target_person_type) or "any"
    scene_type = _normalize_text(payload.scene_type) or "any"
    target_label = TARGET_PERSON_LABELS.get(target_person_type, target_person_type or DEFAULT_SCOPE_LABEL)
    scene_label = SCENE_LABELS.get(scene_type, scene_type or DEFAULT_SCOPE_LABEL)
    scope_label = f"{target_label} · {scene_label}" if target_person_type != "any" or scene_type != "any" else DEFAULT_SCOPE_LABEL
    content = _normalize_text(payload.content)
    if not content:
        raise ReplyCorpusServiceError("语料内容不能为空")

    corpus.title = title or scope_label or DEFAULT_REPLY_CORPUS_TITLE
    corpus.target_person_type = target_person_type
    corpus.scene_type = scene_type
    corpus.corpus_type = scope_label
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


def _corpus_matches_scope(
    corpus: ReplyCorpus,
    target_person_type: str,
    scene_type: str,
) -> tuple[int, bool]:
    corpus_target = _normalize_text(corpus.target_person_type) or "any"
    corpus_scene = _normalize_text(corpus.scene_type) or "any"
    target = _normalize_text(target_person_type) or "any"
    scene = _normalize_text(scene_type) or "any"

    target_match = corpus_target in {"any", target}
    scene_match = corpus_scene in {"any", scene}
    if not target_match or not scene_match:
        return 0, False

    score = 0
    if corpus_target != "any":
        score += 2
    if corpus_scene != "any":
        score += 2
    if corpus_target == target:
        score += 3
    if corpus_scene == scene:
        score += 3
    return score, True


def build_reply_corpus_context(
    db: Session | None = None,
    *,
    target_person_type: str = "",
    scene_type: str = "",
) -> str:
    if db is None:
        return ""

    scored_corpora: list[tuple[int, ReplyCorpus]] = []
    for corpus in _ordered_corpora(db):
        if not corpus.is_enabled or not _normalize_text(corpus.content):
            continue
        score, matched = _corpus_matches_scope(corpus, target_person_type, scene_type)
        if matched:
            scored_corpora.append((score, corpus))

    if not scored_corpora:
        scored_corpora = [
            (0, corpus)
            for corpus in _ordered_corpora(db)
            if corpus.is_enabled and _normalize_text(corpus.content)
        ]

    corpora = [corpus for _, corpus in sorted(scored_corpora, key=lambda item: (item[0], item[1].sort_order, item[1].updated_at, item[1].id), reverse=True)]
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
