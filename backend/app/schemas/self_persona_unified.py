from __future__ import annotations

from pydantic import BaseModel, Field


class SelfPersonaUnifiedLayer(BaseModel):
    summary: str = ""
    points: list[str] = Field(default_factory=list)


class SelfPersonaUnifiedDraft(BaseModel):
    create_mode: str = "standard"
    input_modes: list[str] = Field(default_factory=list)
    work_system: SelfPersonaUnifiedLayer = Field(default_factory=SelfPersonaUnifiedLayer)
    reply_persona: SelfPersonaUnifiedLayer = Field(default_factory=SelfPersonaUnifiedLayer)
    thinking_dna: SelfPersonaUnifiedLayer = Field(default_factory=SelfPersonaUnifiedLayer)
    memory_evidence: SelfPersonaUnifiedLayer = Field(default_factory=SelfPersonaUnifiedLayer)
    reflection_rules: SelfPersonaUnifiedLayer = Field(default_factory=SelfPersonaUnifiedLayer)
