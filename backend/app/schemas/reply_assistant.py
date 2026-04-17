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
    tone_hint: str = ""
    relationship_status: str = ""
    conversation_context: str = ""
    raw_materials: dict[str, Any] = Field(default_factory=dict)


class ReplyAssistantUnderstandingResult(BaseModel):
    meaning_guess: str = ""
    emotion_guess: str = ""
    intent_guess: str = ""
    relationship_state_guess: str = ""
    scene_guess: str = ""
    risk_flags: list[str] = Field(default_factory=list)


class ReplyAssistantReplyCandidate(BaseModel):
    label: str = ""
    text: str = ""
    style_tags: list[str] = Field(default_factory=list)
    reason: str = ""


class ReplyAssistantPredictedReply(BaseModel):
    label: str = ""
    text: str = ""
    risk_level: str = ""


class ReplyAssistantToneProfile(BaseModel):
    label: str = ""
    style_tags: list[str] = Field(default_factory=list)
    guidance: str = ""


class ReplyAssistantResponse(BaseModel):
    mode: str = "reply_assistant"
    target_person_type: str = ""
    target_person_label: str = ""
    scene_type: str = ""
    scene_label: str = ""
    understanding_result: ReplyAssistantUnderstandingResult = Field(default_factory=ReplyAssistantUnderstandingResult)
    reply_candidates: list[ReplyAssistantReplyCandidate] = Field(default_factory=list)
    predicted_replies: list[ReplyAssistantPredictedReply] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    tone_profile: ReplyAssistantToneProfile = Field(default_factory=ReplyAssistantToneProfile)
    recommended_reply: str = ""
    material_summary: str = ""
    context_summary: str = ""
