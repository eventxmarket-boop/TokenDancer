from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReplyCorpusUpsertRequest(BaseModel):
    id: int | None = None
    title: str = Field(default="", max_length=120)
    corpus_type: str = Field(default="高情商回复", max_length=64)
    content: str = Field(default="", min_length=1)
    sort_order: int = 0
    is_enabled: bool = True


class ReplyCorpusPublic(BaseModel):
    id: int
    title: str
    corpus_type: str
    content: str
    sort_order: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class ReplyCorpusDashboardResponse(BaseModel):
    items: list[ReplyCorpusPublic] = Field(default_factory=list)
