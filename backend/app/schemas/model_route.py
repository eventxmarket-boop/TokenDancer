from datetime import datetime
from pydantic import BaseModel


class ModelRouteBase(BaseModel):
    public_model_name: str
    provider_id: int
    provider_model_name: str
    fallback_provider_id: int | None = None
    fallback_model_name: str | None = None
    is_active: bool = True
    priority: int = 100
    cost_multiplier: float = 1.0
    max_context: int | None = None
    notes: str | None = None


class ModelRouteCreate(ModelRouteBase):
    pass


class ModelRouteUpdate(BaseModel):
    public_model_name: str | None = None
    provider_id: int | None = None
    provider_model_name: str | None = None
    fallback_provider_id: int | None = None
    fallback_model_name: str | None = None
    is_active: bool | None = None
    priority: int | None = None
    cost_multiplier: float | None = None
    max_context: int | None = None
    notes: str | None = None


class ModelRouteRead(ModelRouteBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
