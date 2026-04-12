from pydantic import BaseModel
from datetime import datetime


class ProductListItem(BaseModel):
    id: int
    name: str
    slug: str
    category: str
    tag: str | None
    price_cny: float
    stock: int
    delivery_type: str
    product_type: str
    subscription_days: int
    token_quota: int
    is_active: bool
    sort_order: int

    model_config = {"from_attributes": True}


class ProductRead(ProductListItem):
    description: str | None
    price_usd_value: float
    created_at: datetime
    updated_at: datetime | None
