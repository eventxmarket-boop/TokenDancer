from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, DateTime, Numeric, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_mixins import utcnow
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price_cny: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    price_usd_value: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    delivery_type: Mapped[str] = mapped_column(String(50), default="auto")
    product_type: Mapped[str] = mapped_column(String(50), default="balance_topup")  # balance_topup | subscription | token_pack
    subscription_days: Mapped[int] = mapped_column(Integer, default=0)           # 订阅天数（subscription 类型）
    token_quota: Mapped[int] = mapped_column(Integer, default=0)                 # token配额（token_pack 类型）
    tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
