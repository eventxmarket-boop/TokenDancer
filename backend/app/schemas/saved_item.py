from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SavedItemUpsert(BaseModel):
    item_key: str = Field(min_length=1, max_length=128)
    title: str = ""
    pinned: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)


class SavedItemBatchReplaceRequest(BaseModel):
    items: list[SavedItemUpsert] = Field(default_factory=list)


class SavedItemRead(BaseModel):
    item_key: str
    title: str
    pinned: bool
    payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime
