from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RelationshipManagementProfile(BaseModel):
    relationship_type: str = ""
    name: str = ""
    relationship_stage: str = ""
    tone: str = ""
    response_temperature: str = ""
    catchphrases: list[str] = Field(default_factory=list)
    boundaries: str = ""
    analysis_focus: str = ""
    understanding_weight: float = 0.0
    maintenance_weight: float = 0.0
    message_push_weight: float = 0.0


class RelationshipManagementMemoryBase(BaseModel):
    relationship_memory: list[str] = Field(default_factory=list)
    interaction_samples: list[str] = Field(default_factory=list)
    style_samples: list[str] = Field(default_factory=list)
    candidate_reply_cues: list[str] = Field(default_factory=list)
    relationship_context: str = ""
    analysis_focus: str = ""
    understanding_weight: float = 0.0
    maintenance_weight: float = 0.0
    message_push_weight: float = 0.0
    message_push_cues: list[str] = Field(default_factory=list)
    raw_materials: dict[str, Any] = Field(default_factory=dict)
