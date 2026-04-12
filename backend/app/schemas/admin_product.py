from typing import Optional
from pydantic import BaseModel


class AdminProductCreate(BaseModel):
    name: str
    slug: str
    category: str
    description: Optional[str] = None
    tag: Optional[str] = None
    price_cny: float
    price_usd_value: float
    stock: int
    delivery_type: str
    product_type: str = "balance_topup"
    subscription_days: int = 0
    token_quota: int = 0
    is_active: bool = True
    sort_order: int = 0


class AdminProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    tag: Optional[str] = None
    price_cny: Optional[float] = None
    price_usd_value: Optional[float] = None
    stock: Optional[int] = None
    delivery_type: Optional[str] = None
    product_type: Optional[str] = None
    subscription_days: Optional[int] = None
    token_quota: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
