from datetime import datetime
from pydantic import BaseModel


class RoutePolicyBase(BaseModel):
    name: str
    public_model_name: str
    primary_provider_id: int
    secondary_provider_id: int | None = None
    policy_type: str = "fixed"
    retry_count: int = 1
    cooldown_seconds: int = 60
    timeout_seconds: int = 60
    is_active: bool = True
    notes: str | None = None


class RoutePolicyCreate(RoutePolicyBase):
    pass


class RoutePolicyUpdate(BaseModel):
    name: str | None = None
    public_model_name: str | None = None
    primary_provider_id: int | None = None
    secondary_provider_id: int | None = None
    policy_type: str | None = None
    retry_count: int | None = None
    cooldown_seconds: int | None = None
    timeout_seconds: int | None = None
    is_active: bool | None = None
    notes: str | None = None


class RoutePolicyRead(RoutePolicyBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
