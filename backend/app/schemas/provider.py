from datetime import datetime

from pydantic import BaseModel, field_validator

from app.core.constants import VALID_PROVIDER_TYPES


class ProviderBase(BaseModel):
    name: str
    provider_type: str
    base_url: str | None = None
    is_active: bool = True
    priority: int = 100
    timeout_seconds: int = 60
    notes: str | None = None

    @field_validator("provider_type")
    @classmethod
    def validate_provider_type(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized not in VALID_PROVIDER_TYPES:
            raise ValueError(f"非法 provider_type，可选: {', '.join(sorted(VALID_PROVIDER_TYPES))}")
        return normalized


class ProviderCreate(ProviderBase):
    pass


class ProviderUpdate(BaseModel):
    name: str | None = None
    provider_type: str | None = None
    base_url: str | None = None
    is_active: bool | None = None
    priority: int | None = None
    timeout_seconds: int | None = None
    health_status: str | None = None
    notes: str | None = None

    @field_validator("provider_type")
    @classmethod
    def validate_provider_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in VALID_PROVIDER_TYPES:
            raise ValueError(f"非法 provider_type，可选: {', '.join(sorted(VALID_PROVIDER_TYPES))}")
        return normalized


class ProviderRead(ProviderBase):
    id: int
    health_status: str
    last_health_check_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
