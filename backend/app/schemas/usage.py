from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator


class UsageRecordBase(BaseModel):
    api_key_id: int
    model_name: str


class UsageRecordCreate(UsageRecordBase):
    user_id: int
    public_model_name: str | None = None
    provider_id: int | None = None
    provider_key_id: int | None = None
    upstream_model_name: str | None = None
    request_status: str = "success"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: Decimal = Decimal("0")
    cost_amount: Decimal = Decimal("0")
    latency_ms: int = 0


class UsageRecordRead(BaseModel):
    id: int
    api_key_id: int
    model_name: str
    public_model_name: str | None = None
    provider_id: int | None = None
    provider_key_id: int | None = None
    upstream_model_name: str | None = None
    request_status: str = "success"
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    cost_amount: float | None = None
    latency_ms: int
    requested_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("cost", mode="before")
    @classmethod
    def convert_cost(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v
