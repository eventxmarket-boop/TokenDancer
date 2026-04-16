from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.create_wizard import CreateWizardDraft


class CreatedPersonaSaveRequest(BaseModel):
    draft: CreateWizardDraft
    source_type: str = "create_wizard"
    status: str = "saved"


class CreatedPersonaSummary(BaseModel):
    id: int
    user_id: int | None = None
    slug: str
    name: str
    persona_type: str
    entry_label: str = ""
    input_mode: str = ""
    family_subtype: str = ""
    analysis_focus: str = ""
    understanding_weight: float = 0.0
    maintenance_weight: float = 0.0
    summary: str
    material_summary: str = ""
    status: str
    source_type: str
    created_at: datetime
    updated_at: datetime


class CreatedPersonaRecord(CreatedPersonaSummary):
    draft_payload: CreateWizardDraft


class CreatedPersonaListResponse(BaseModel):
    items: list[CreatedPersonaSummary] = Field(default_factory=list)


class CreatedPersonaDetailResponse(BaseModel):
    item: CreatedPersonaRecord
