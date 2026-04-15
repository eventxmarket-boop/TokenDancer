from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    persona_slug: str = Field(min_length=1)
    session_id: str | None = None
    message: str = Field(min_length=1)


class ChatUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    session_id: str
    persona_slug: str
    title: str = ""
    reply: str
    model: str
    usage: ChatUsage
    latency_ms: int


class ChatSessionClearResponse(BaseModel):
    session_id: str
    status: str = "cleared"


class ChatMessageRecord(BaseModel):
    role: str
    content: str
    model: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    created_at: datetime


class ChatSessionDetailResponse(BaseModel):
    session_id: str
    persona_slug: str
    title: str = ""
    messages: list[ChatMessageRecord] = Field(default_factory=list)


class RecentSessionSummary(BaseModel):
    id: str
    persona_slug: str
    persona_name: str
    title: str
    updated_at: datetime
