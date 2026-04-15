from __future__ import annotations

from pydantic import BaseModel, Field


class ReunionPersonaProfile(BaseModel):
    relationship_type: str = ""
    name: str = ""
    tone: str = ""
    remembrance_style: str = ""
    comfort_style: str = ""
    boundaries: str = ""


class ReunionPersonaMemoryBase(BaseModel):
    chat_history_summary: str = ""
    diary_notes: list[str] = Field(default_factory=list)
    letter_notes: list[str] = Field(default_factory=list)
    photo_notes: list[str] = Field(default_factory=list)
    voice_notes: list[str] = Field(default_factory=list)
    memory_fragments: list[str] = Field(default_factory=list)
    shared_memories: list[str] = Field(default_factory=list)


class ReunionPersonaRetrievalPolicy(BaseModel):
    mode: str = ""
    progressive_recall: bool = True
    priority_rules: list[str] = Field(default_factory=list)
    fallback_rules: list[str] = Field(default_factory=list)


class ReunionPersonaSafetyGuardrails(BaseModel):
    boundaries: list[str] = Field(default_factory=list)
    emotional_protection: list[str] = Field(default_factory=list)
    avoid_triggers: list[str] = Field(default_factory=list)
