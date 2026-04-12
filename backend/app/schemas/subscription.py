from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class SubscriptionRead(BaseModel):
    id: int
    user_id: int
    product_id: Optional[int]
    plan_name: str
    status: str
    starts_at: datetime
    expires_at: datetime
    source_order_id: Optional[int]
    created_at: datetime
    model_config = {"from_attributes": True}


class TokenGrantRead(BaseModel):
    id: int
    user_id: int
    product_id: Optional[int]
    quota: int
    used: int
    status: str
    source_order_id: Optional[int]
    expires_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}
