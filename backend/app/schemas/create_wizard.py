from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.family_companion import (
    FamilyCompanionGuidedMemoryAnswers,
    FamilyCompanionMemoryBase,
    FamilyCompanionPersonaProfile,
)
from app.schemas.intimate_companion import (
    IntimateCompanionMemoryBase,
    IntimateCompanionRelationshipProfile,
)
from app.schemas.reunion_persona import (
    ReunionPersonaMemoryBase,
    ReunionPersonaProfile,
    ReunionPersonaRetrievalPolicy,
    ReunionPersonaSafetyGuardrails,
)
from app.schemas.self_persona_unified import SelfPersonaUnifiedDraft


class FamilyCompanionUploadedImageDocument(BaseModel):
    filename: str = ""
    mime_type: str = ""
    size: int = 0
    data_url: str = ""


class FamilyCompanionRawMaterials(BaseModel):
    chat_history_text: str = ""
    memory_notes_text: str = ""
    text_materials_text: str = ""
    uploaded_text_documents: list[dict[str, Any]] = Field(default_factory=list)
    uploaded_image_documents: list[FamilyCompanionUploadedImageDocument] = Field(default_factory=list)
    image_notes_text: str = ""
    photo_notes_text: str = ""
    voice_notes_text: str = ""


class CreateWizardDraftRequest(BaseModel):
    create_type: str
    group: str = ""
    source_repo: str = ""
    display_name: str = ""
    create_mode: str = ""
    input_mode: str
    family_subtype: str = ""
    input_modes: list[str] = Field(default_factory=list)
    schema_key: str = ""
    raw_materials: FamilyCompanionRawMaterials = Field(default_factory=FamilyCompanionRawMaterials)
    form_data: dict[str, Any] = Field(default_factory=dict)
    guided_memory_answers: FamilyCompanionGuidedMemoryAnswers = Field(default_factory=FamilyCompanionGuidedMemoryAnswers)


class CreateWizardDraftMeta(BaseModel):
    id: str
    slug: str
    name: str
    category: str
    display_name: str = ""
    version: str
    status: str
    create_type: str
    create_mode: str = ""
    input_mode: str
    family_subtype: str = ""
    input_modes: list[str] = Field(default_factory=list)
    group: str
    schema_key: str = ""
    source_repo: str
    repo_url: str
    source_repos: list[str] = Field(default_factory=list)
    source_hint: str = ""
    stage: str = "draft"
    persona_kind: str = "create"
    generated_at: str = ""


class CreateWizardDraft(BaseModel):
    meta: CreateWizardDraftMeta
    profile: str
    mindset: str
    heuristics: str
    expression: str
    guardrails: str
    relationship_type: str = ""
    family_subtype: str = ""
    raw_materials: dict[str, Any] | None = None
    guided_memory_answers: FamilyCompanionGuidedMemoryAnswers | None = None
    emotion_rules: dict[str, Any] | None = None
    self_persona_unified: SelfPersonaUnifiedDraft | None = None
    persona_profile: FamilyCompanionPersonaProfile | None = None
    memory_base: FamilyCompanionMemoryBase | None = None
    reunion_persona_profile: ReunionPersonaProfile | None = None
    reunion_memory_base: ReunionPersonaMemoryBase | None = None
    reunion_memory_retrieval_policy: ReunionPersonaRetrievalPolicy | None = None
    reunion_safety_guardrails: ReunionPersonaSafetyGuardrails | None = None
    relationship_profile: IntimateCompanionRelationshipProfile | None = None
    intimate_memory_base: IntimateCompanionMemoryBase | None = None
    intimate_understanding: dict[str, Any] | None = None
    intimate_message_simulation: dict[str, Any] | None = None
    intimate_relationship_maintenance: dict[str, Any] | None = None
    intimate_past_relationship: dict[str, Any] | None = None


class CreateWizardDraftResponse(BaseModel):
    draft: CreateWizardDraft
