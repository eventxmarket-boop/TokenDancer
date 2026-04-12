from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PaymentIntentCreate(BaseModel):
    order_id: int
    payment_method: str = "alipay_qr"


class PaymentIntentResponse(BaseModel):
    payment_id: str
    order_id: int
    amount: float
    currency: str
    status: str  # pending | paid | failed
    payment_url: Optional[str] = None
    created_at: datetime


class PaymentWebhookRequest(BaseModel):
    event_type: str
    payment_id: str
    order_id: int
    status: str
    signature: Optional[str] = None


class PaymentStatus(BaseModel):
    order_id: int
    payment_id: Optional[str]
    status: str  # pending | paid | failed | cancelled
    paid_at: Optional[datetime] = None
