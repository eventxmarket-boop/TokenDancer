from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator


class RedeemCodeBase(BaseModel):
    code: str


class RedeemCodeCreate(RedeemCodeBase):
    reward_type: str = "balance"
    reward_amount: Decimal = Decimal("0")
    expires_at: datetime | None = None


class RedeemCodeRead(RedeemCodeBase):
    id: int
    reward_type: str
    reward_amount: Decimal
    is_used: int
    used_by: int | None
    used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RedeemRequest(BaseModel):
    code: str


class RedeemResponse(BaseModel):
    success: bool
    message: str
    balance_delta: float


class RedeemLogBase(BaseModel):
    code: str
    status: str = "成功"


class RedeemLogCreate(RedeemLogBase):
    user_id: int
    message: str | None = None
    balance_delta: Decimal = Decimal("0")


class RedeemLogRead(BaseModel):
    id: int
    code: str
    status: str
    message: str | None
    balance_delta: float
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("balance_delta", mode="before")
    @classmethod
    def convert_balance_delta(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v
