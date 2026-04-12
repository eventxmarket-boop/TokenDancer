from datetime import datetime

from pydantic import BaseModel, field_validator

from app.core.constants import VALID_ROUTE_POLICY_TYPES


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

    @field_validator("policy_type")
    @classmethod
    def validate_policy_type(cls, value: str) -> str:
        normalized = (value or "fixed").strip().lower()
        if normalized not in VALID_ROUTE_POLICY_TYPES:
            raise ValueError(f"非法 policy_type，可选: {', '.join(sorted(VALID_ROUTE_POLICY_TYPES))}")
        return normalized


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

    @field_validator("policy_type")
    @classmethod
    def validate_policy_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in VALID_ROUTE_POLICY_TYPES:
            raise ValueError(f"非法 policy_type，可选: {', '.join(sorted(VALID_ROUTE_POLICY_TYPES))}")
        return normalized


class RoutePolicyRead(RoutePolicyBase):
    id: int
    created_at: datetime
    primary_provider_name: str | None = None
    secondary_provider_name: str | None = None
    linked_route_id: int | None = None
    route_ready: bool = False
    route_provider_pair_valid: bool = False

    model_config = {"from_attributes": True}
