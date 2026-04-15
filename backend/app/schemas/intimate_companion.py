from __future__ import annotations

from pydantic import BaseModel, Field


class IntimateCompanionRelationshipProfile(BaseModel):
    relationship_type: str = ""
    name: str = ""
    relationship_stage: str = ""
    tone: str = ""
    response_temperature: str = ""
    catchphrases: list[str] = Field(default_factory=list)
    boundaries: str = ""


class IntimateCompanionMemoryBase(BaseModel):
    conversation_samples: list[str] = Field(default_factory=list)
    interaction_rules: list[str] = Field(default_factory=list)
    relationship_goals: list[str] = Field(default_factory=list)
    key_memories: list[str] = Field(default_factory=list)
