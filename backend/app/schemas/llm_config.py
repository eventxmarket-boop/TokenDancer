from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LLMConfigUpsertRequest(BaseModel):
    id: int | None = None
    provider: str = Field(default="openai_compatible", min_length=1)
    base_url: str = Field(default="https://api.openai.com/v1", min_length=1)
    api_key: str = Field(default="")
    model_name: str = Field(default="gpt-5.4-mini", min_length=1)
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=800, ge=1)
    is_default: bool = True
    is_enabled: bool = True


class LLMConfigPublic(BaseModel):
    id: int
    provider: str
    base_url: str
    api_key_masked: str = ""
    model_name: str
    temperature: float
    max_tokens: int
    is_default: bool
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class LLMConfigDashboardResponse(BaseModel):
    current: LLMConfigPublic | None = None
    items: list[LLMConfigPublic] = Field(default_factory=list)
