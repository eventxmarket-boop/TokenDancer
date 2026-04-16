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
    episodic_memories: list[str] = Field(default_factory=list)
    semantic_memories: list[str] = Field(default_factory=list)
    procedural_memories: list[str] = Field(default_factory=list)
    legacy_summary: list[str] = Field(default_factory=list)
    episodic_count: int = 0
    semantic_count: int = 0
    procedural_count: int = 0
    chat_history_summary: str = ""
    diary_notes: list[str] = Field(default_factory=list)
    letter_notes: list[str] = Field(default_factory=list)
    photo_notes: list[str] = Field(default_factory=list)
    voice_notes: list[str] = Field(default_factory=list)
    memory_fragments: list[str] = Field(default_factory=list)
    shared_memories: list[str] = Field(default_factory=list)
    guided_memory_answers: dict[str, str] = Field(default_factory=dict)


class ReunionPersonaGuidedMemoryAnswers(BaseModel):
    recall_scenes: str = ""
    how_they_addressed_you: str = ""
    repeated_phrases: str = ""
    most_characteristic_moment: str = ""
    deepest_impression: str = ""
    care_style: str = ""
    typical_reminders: str = ""
    most_important_shared_memory: str = ""


class ReunionPersonaRetrievalPolicy(BaseModel):
    mode: str = ""
    progressive_recall: bool = True
    recall_stage: str = ""
    priority_rules: list[str] = Field(default_factory=list)
    fallback_rules: list[str] = Field(default_factory=list)
    max_memory_items: int = 4
    emotion_weight: float = 0.35
    topic_weight: float = 0.35
    layer_weight: float = 0.2
    safety_weight: float = 0.1


class ReunionPersonaSafetyGuardrails(BaseModel):
    boundaries: list[str] = Field(default_factory=list)
    emotional_protection: list[str] = Field(default_factory=list)
    avoid_triggers: list[str] = Field(default_factory=list)
    avoid_dependency_language: bool = True
    avoid_claiming_certainty: bool = True
    avoid_afterlife_claims: bool = True
    de_escalate_distress: bool = True
