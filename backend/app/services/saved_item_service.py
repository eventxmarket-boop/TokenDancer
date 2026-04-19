from __future__ import annotations

import json
import re
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.saved_item import SavedItem
from app.schemas.saved_item import SavedItemRead, SavedItemUpsert


KIND_PATTERN = re.compile(r"^[a-z0-9_-]{1,40}$")


def _normalize_kind(kind: str) -> str:
    value = (kind or "").strip().lower()
    if not value or not KIND_PATTERN.match(value):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="保存类型不合法")
    return value


def _normalize_key(item_key: str) -> str:
    value = (item_key or "").strip()
    if not value:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="保存项标识不能为空")
    return value[:128]


def _normalize_title(title: str) -> str:
    return (title or "").strip()[:160]


def _payload_to_text(payload: dict[str, Any]) -> str:
    try:
        return json.dumps(payload or {}, ensure_ascii=False, default=str)
    except TypeError:
        return json.dumps({}, ensure_ascii=False)


def _payload_from_text(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _row_to_read(row: SavedItem) -> SavedItemRead:
    return SavedItemRead(
        item_key=row.item_key,
        title=row.title,
        pinned=bool(row.pinned),
        payload=_payload_from_text(row.payload_json),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def list_saved_items(db: Session, user_id: int, kind: str) -> list[SavedItemRead]:
    normalized_kind = _normalize_kind(kind)
    rows = (
        db.query(SavedItem)
        .filter(SavedItem.user_id == user_id, SavedItem.kind == normalized_kind)
        .order_by(SavedItem.pinned.desc(), SavedItem.updated_at.desc(), SavedItem.id.desc())
        .all()
    )
    return [_row_to_read(row) for row in rows]


def replace_saved_items(db: Session, user_id: int, kind: str, items: list[SavedItemUpsert]) -> list[SavedItemRead]:
    normalized_kind = _normalize_kind(kind)
    existing_rows = (
        db.query(SavedItem)
        .filter(SavedItem.user_id == user_id, SavedItem.kind == normalized_kind)
        .all()
    )
    existing_map = {row.item_key: row for row in existing_rows}
    next_keys: set[str] = set()

    for item in items:
        item_key = _normalize_key(item.item_key)
        next_keys.add(item_key)
        row = existing_map.get(item_key)
        if row is None:
            row = SavedItem(
                user_id=user_id,
                kind=normalized_kind,
                item_key=item_key,
            )
            db.add(row)

        row.title = _normalize_title(item.title) or item_key
        row.pinned = bool(item.pinned)
        row.payload_json = _payload_to_text(item.payload)

    for row in existing_rows:
        if row.item_key not in next_keys:
            db.delete(row)

    db.commit()
    return list_saved_items(db, user_id, normalized_kind)


def clear_saved_items(db: Session, user_id: int, kind: str) -> None:
    normalized_kind = _normalize_kind(kind)
    (
        db.query(SavedItem)
        .filter(SavedItem.user_id == user_id, SavedItem.kind == normalized_kind)
        .delete(synchronize_session=False)
    )
    db.commit()
