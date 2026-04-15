from pydantic import BaseModel, Field


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
    reply: str
    model: str
    usage: ChatUsage
    latency_ms: int


class ChatSessionClearResponse(BaseModel):
    session_id: str
    status: str = "cleared"
