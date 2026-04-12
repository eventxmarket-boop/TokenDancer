from pydantic import BaseModel
from datetime import datetime


class CartItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_slug: str
    delivery_type: str
    category: str
    quantity: int
    unit_price: float
    created_at: datetime

    model_config = {"from_attributes": True}


class CartRead(BaseModel):
    id: int
    user_id: int
    coupon_code: str | None
    items: list[CartItemRead]
    subtotal: float
    total_quantity: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CouponUpdate(BaseModel):
    coupon_code: str
