from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReplyAssistantRequest(BaseModel):
    message: str = Field(min_length=1)
    target_person_type: str = ""
    target_person_label: str = ""
    scene_type: str = ""
    current_context: str = ""
    target_goal: str = ""
    relationship_status: str = ""
    conversation_context: str = ""
    rewrite_mode: str = "default"
    tone_hint: str = ""
    raw_materials: dict[str, Any] = Field(default_factory=dict)


class ReplyAssistantAnalysisResult(BaseModel):
    meaning_guess: str = ""
    emotion_guess: str = ""
    intent_guess: str = ""
    relationship_state_guess: str = ""
    scene_guess: str = ""
    risk_flags: list[str] = Field(default_factory=list)
    tone_constraints: list[str] = Field(default_factory=list)
    person_type_bias: str = ""
    scene_bias: str = ""


class ReplyAssistantResponse(BaseModel):
    mode: str = "reply_assistant"
    judgment: str = ""
    recommended_reply: str = ""
    risk_note: str = ""
    likely_consequence: str = ""
