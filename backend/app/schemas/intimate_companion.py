from __future__ import annotations

from typing import Any

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
    relationship_context: str = ""
    misunderstanding_points: list[str] = Field(default_factory=list)
    rewrite_targets: list[str] = Field(default_factory=list)
    target_persona_profile: dict[str, Any] = Field(default_factory=dict)
    conversation_context: dict[str, Any] = Field(default_factory=dict)
    reply_style_samples: list[str] = Field(default_factory=list)
    simulation_preferences: dict[str, Any] = Field(default_factory=dict)
    interaction_patterns: list[str] = Field(default_factory=list)
    maintenance_goals: list[str] = Field(default_factory=list)
    relationship_memory: list[str] = Field(default_factory=list)
    expression_samples: list[str] = Field(default_factory=list)
    response_temperature: str = ""
    boundaries: list[str] = Field(default_factory=list)
