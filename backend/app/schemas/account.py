from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class LedgerEntry(BaseModel):
    id: int
    user_id: int
    operation: str
    amount: float
    balance_before: float
    balance_after: float
    redeem_log_id: Optional[int] = None
    usage_record_id: Optional[int] = None
    order_id: Optional[int] = None
    remark: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BalanceSnapshot(BaseModel):
    balance: float
    available_balance: float


# ---- Usage record creation (used by internal / proxy layer) ----

class UsageRecordCreate(BaseModel):
    api_key_id: int
    model_name: str = "unknown"
    public_model_name: str | None = None
    provider_id: int | None = None
    provider_key_id: int | None = None
    upstream_model_name: str | None = None
    request_status: str = "success"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = Field(default=0)
    cost: float = Field(default=0.0, ge=0)
    cost_amount: float = Field(default=0.0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    # deduct_balance: 是否真实扣费（测试时可为 False）
    deduct_balance: bool = True


class UsageRecordRead(BaseModel):
    id: int
    user_id: int
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
