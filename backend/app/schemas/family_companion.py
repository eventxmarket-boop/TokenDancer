from __future__ import annotations

from pydantic import BaseModel, Field


class FamilyCompanionPersonaProfile(BaseModel):
    relationship_type: str = ""
    name: str = ""
    tone: str = ""
    catchphrases: list[str] = Field(default_factory=list)
    comfort_style: str = ""
    celebration_style: str = ""
    boundaries: str = ""


class FamilyCompanionMemoryBase(BaseModel):
    shared_events: list[str] = Field(default_factory=list)
    important_advice: list[str] = Field(default_factory=list)
    daily_habits: list[str] = Field(default_factory=list)
    emotional_triggers: list[str] = Field(default_factory=list)
    chat_history_summary: str = ""
    memory_fragments: list[str] = Field(default_factory=list)
    text_materials: list[str] = Field(default_factory=list)
    image_notes: list[str] = Field(default_factory=list)
    voice_notes: list[str] = Field(default_factory=list)
