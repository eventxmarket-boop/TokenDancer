from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


HowToDoSection = Literal["cast", "reference", "catalog", "calendar", "clock", "records", "songs"]
HowToDoCastMode = Literal["character", "number", "coin", "taiji"]


class HowToDoRequest(BaseModel):
    section: HowToDoSection = "cast"
    cast_mode: HowToDoCastMode = "coin"
    question: str = ""
    cast_seed: str = ""
    character_text: str = ""
    number_text: str = ""
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
