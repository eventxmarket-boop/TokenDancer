from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


HowToDoMode = Literal["zhouyi", "liuyao", "bazi"]
HowToDoLiuYaoCastMode = Literal["time", "manual"]


class HowToDoRequest(BaseModel):
    mode: HowToDoMode = "zhouyi"
    question: str = ""
    cast_seed: str = ""
    liuyao_cast_mode: HowToDoLiuYaoCastMode = "time"
    liuyao_lines: list[int] = Field(default_factory=list)
    birth_year: int | None = None
    birth_month: int | None = None
    birth_day: int | None = None
    birth_hour: int | None = None
    gender: Literal["male", "female"] | str = ""
    use_ai: bool = True


class HowToDoCard(BaseModel):
    label: str = ""
    value: str = ""


class HowToDoResponse(BaseModel):
    mode: str = ""
    method_label: str = ""
    question: str = ""
    summary: str = ""
    cards: list[HowToDoCard] = Field(default_factory=list)
    ai_interpretation: str = ""
    suggestions: list[str] = Field(default_factory=list)
    raw_result: dict[str, Any] = Field(default_factory=dict)
    model_used: str = ""
