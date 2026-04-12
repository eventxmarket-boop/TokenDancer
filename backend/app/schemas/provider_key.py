from datetime import datetime
from pydantic import BaseModel


class ProviderKeyBase(BaseModel):
    provider_id: int
    name: str
    supported_models: str | None = None
    status: str = "active"
    weight: int = 1
    rpm_limit: int = 1000
    daily_limit: int = 100000
    notes: str | None = None


class ProviderKeyCreate(BaseModel):
    provider_id: int
    name: str
    api_key: str  # the real key, will be encrypted and masked
    supported_models: str | None = None
    status: str = "active"
    weight: int = 1
    rpm_limit: int = 1000
    daily_limit: int = 100000
    notes: str | None = None


class ProviderKeyUpdate(BaseModel):
    name: str | None = None
    api_key: str | None = None  # optional update
    supported_models: str | None = None
    status: str | None = None
    weight: int | None = None
    rpm_limit: int | None = None
    daily_limit: int | None = None
    notes: str | None = None


class ProviderKeyRead(ProviderKeyBase):
    id: int
    key_masked: str  # NEVER the real key
    used_count_today: int
    last_used_at: datetime | None
    last_error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
