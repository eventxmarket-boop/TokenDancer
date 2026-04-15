from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateWizardDraftRequest(BaseModel):
    create_type: str
    input_mode: str
    form_data: dict[str, Any] = Field(default_factory=dict)


class CreateWizardDraftMeta(BaseModel):
    id: str
    slug: str
    name: str
    category: str
    version: str
    status: str
    create_type: str
    input_mode: str
    group: str
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


class CreateWizardDraftResponse(BaseModel):
    draft: CreateWizardDraft
