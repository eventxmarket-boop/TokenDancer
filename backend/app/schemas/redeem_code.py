from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class RedeemCodeCreate(BaseModel):
    code: Optional[str] = Field(default=None, description="不传则自动生成")
    reward_type: str = Field(default="balance", description="'balance' 或 'concurrent_limit'")
    reward_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    expires_at: Optional[datetime] = None


class RedeemCodeRead(BaseModel):
    id: int
    code: str
    reward_type: str
    reward_amount: float
    is_used: bool
    used_by: Optional[int] = None
    used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class RedeemCodeFilter(BaseModel):
    is_used: Optional[bool] = None
    is_expired: Optional[bool] = None


class RedeemCodeUpdate(BaseModel):
    expires_at: Optional[datetime] = None
