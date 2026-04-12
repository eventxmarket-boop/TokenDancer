from pydantic import BaseModel
from datetime import datetime


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderListItem(BaseModel):
    id: int
    order_no: str
    status: str
    total_amount: float
    payment_method: str | None
    user_email: str | None
    user_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderRead(OrderListItem):
    coupon_code: str | None
    items: list[OrderItemRead]
    updated_at: datetime | None
    user_email: str | None = None
    user_id: int | None = None

    model_config = {"from_attributes": True}
