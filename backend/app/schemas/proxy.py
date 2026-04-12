from pydantic import BaseModel, Field
from typing import Optional


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="public model name, e.g. gpt-4o")
    messages: list[ChatMessage]
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=1024, ge=1)
    stream: bool = Field(default=False)
    user: Optional[str] = None


class DebugInfo(BaseModel):
    public_model: Optional[str] = None
    provider_name: Optional[str] = None
    provider_type: Optional[str] = None
    provider_id: Optional[int] = None
    provider_key_id: Optional[int] = None
    policy_type: Optional[str] = None
    fallback_used: Optional[bool] = None
    fallback_triggered: Optional[bool] = None
    provider_switch_count: Optional[int] = None
    key_switch_count: Optional[int] = None
    latency_ms: Optional[float] = None
    cost: Optional[float] = None
    total_tokens: Optional[int] = None
    upstream_model_name: Optional[str] = None
    failure_chain_summary: Optional[str] = None


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: Optional[dict] = None
    debug: Optional[DebugInfo] = None
