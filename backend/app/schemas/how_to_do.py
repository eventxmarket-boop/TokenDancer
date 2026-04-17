from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


HowToDoSection = Literal["cast", "sundial", "catalog", "songs", "detail"]
HowToDoCastMode = Literal["manual", "character", "coin", "taiji"]


class HowToDoRequest(BaseModel):
    section: HowToDoSection = "cast"
    cast_mode: HowToDoCastMode = "coin"
    question: str = ""
    category: str = ""
    cast_seed: str = ""
    manual_lines: list[int] = Field(default_factory=list)
    character_text: str = ""
    use_ai: bool = True
    selected_hexagram: str = ""


class HowToDoCard(BaseModel):
    label: str = ""
    value: str = ""


class HowToDoCatalogCard(BaseModel):
    number: int = 0
    name: str = ""
    meaning: str = ""
    binary: str = ""
    palace: str = ""
    tag: str = ""


class HowToDoResponse(BaseModel):
    section: str = ""
    method_label: str = ""
    question: str = ""
    summary: str = ""
    cards: list[HowToDoCard] = Field(default_factory=list)
    ai_interpretation: str = ""
    suggestions: list[str] = Field(default_factory=list)
    raw_result: dict[str, Any] = Field(default_factory=dict)
    catalog: list[HowToDoCatalogCard] = Field(default_factory=list)
    model_used: str = ""
