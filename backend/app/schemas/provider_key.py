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
    api_key: str
    supported_models: str | None = None
    status: str = "active"
    weight: int = 1
    rpm_limit: int = 1000
    daily_limit: int = 100000
    notes: str | None = None


class ProviderKeyUpdate(BaseModel):
    provider_id: int | None = None
    name: str | None = None
    api_key: str | None = None
    supported_models: str | None = None
    status: str | None = None
    weight: int | None = None
    rpm_limit: int | None = None
    daily_limit: int | None = None
    notes: str | None = None


class ProviderKeyRead(ProviderKeyBase):
    id: int
    key_masked: str
    used_count_today: int
    last_used_at: datetime | None
    last_error: str | None
    created_at: datetime
    provider_name: str | None = None
    provider_type: str | None = None
    provider_health_status: str | None = None
    request_count_24h: int = 0
    success_count_24h: int = 0
    failure_count_24h: int = 0

    model_config = {"from_attributes": True}
