from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.family_companion import FamilyCompanionMemoryBase, FamilyCompanionPersonaProfile
from app.schemas.intimate_companion import (
    IntimateCompanionMemoryBase,
    IntimateCompanionRelationshipProfile,
)


class CreateWizardDraftRequest(BaseModel):
    create_type: str
    group: str = ""
    source_repo: str = ""
    display_name: str = ""
    input_mode: str
    schema_key: str = ""
    form_data: dict[str, Any] = Field(default_factory=dict)


class CreateWizardDraftMeta(BaseModel):
    id: str
    slug: str
    name: str
    category: str
    display_name: str = ""
    version: str
    status: str
    create_type: str
    input_mode: str
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
    persona_profile: FamilyCompanionPersonaProfile | None = None
    memory_base: FamilyCompanionMemoryBase | None = None
    relationship_profile: IntimateCompanionRelationshipProfile | None = None
    intimate_memory_base: IntimateCompanionMemoryBase | None = None


class CreateWizardDraftResponse(BaseModel):
    draft: CreateWizardDraft
