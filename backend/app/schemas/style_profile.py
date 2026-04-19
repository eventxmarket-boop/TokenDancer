from __future__ import annotations

from pydantic import BaseModel, Field


class StyleProfileSelection(BaseModel):
    mbti_type: str = ""
    zodiac_sign: str = ""


class StyleProfileDimensions(BaseModel):
    depth: str = ""
    humor: str = ""
    directness: str = ""
    warmth: str = ""
    pace: str = ""
    structure: str = ""
    boundary: str = ""
    decision_style: str = ""


class StyleProfileDraft(BaseModel):
    selection: StyleProfileSelection = Field(default_factory=StyleProfileSelection)
    summary: str = ""
    points: list[str] = Field(default_factory=list)
    dimensions: StyleProfileDimensions = Field(default_factory=StyleProfileDimensions)
    mbti_traits: list[str] = Field(default_factory=list)
    zodiac_traits: list[str] = Field(default_factory=list)
    conflict_notes: list[str] = Field(default_factory=list)
