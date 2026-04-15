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
