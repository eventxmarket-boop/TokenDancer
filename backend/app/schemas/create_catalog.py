from pydantic import BaseModel, Field


class CreateCatalogItem(BaseModel):
    slug: str
    name: str
    group: str
    create_type: str = ""
    source_repo: str
    repo_url: str
    description: str
    input_modes: list[str] = Field(default_factory=list)
    stage: str
    entry_type: str = "create"
    ui_mode: str = "card"
    status: str = "available"
    sort_order: int = 0


class CreateCatalogGroup(BaseModel):
    group: str
    label: str
    description: str
    source_hint: str
    sort_order: int = 0
    items: list[CreateCatalogItem] = Field(default_factory=list)


class CreateCatalogResponse(BaseModel):
    version: str
    updated_at: str
    groups: list[CreateCatalogGroup] = Field(default_factory=list)
