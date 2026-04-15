from pydantic import BaseModel, Field


class PersonaRecord(BaseModel):
    id: str
    slug: str
    name: str
    category: str
    version: str
    status: str
    avatar: str | None = None
    tags: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    isSeed: bool = False
    seedSource: str = ""
    seedGroup: str = ""
    isFeatured: bool = False
    isFavoritable: bool = True
    personaKind: str = "seed"
    intro: str = ""
    profile: str = ""
    recommendedQuestions: list[str] = Field(default_factory=list)
    mindset: str = ""
    heuristics: str = ""
    expression: str = ""
    persona_examples: str = ""
    state: str = ""
    guardrails: str = ""
