from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SelfFillAssistantRequest(BaseModel):
    message: str = Field(min_length=1)
    create_mode: str = ""
    current_step: str = ""
    active_section: str = ""
    active_field_key: str = ""
    active_field_label: str = ""
    field_context: str = ""
    conversation_context: str = ""
    form_snapshot: dict[str, Any] = Field(default_factory=dict)


class SelfFillAssistantResponse(BaseModel):
    mode: str = "self_fill_assistant"
    reply: str = ""
