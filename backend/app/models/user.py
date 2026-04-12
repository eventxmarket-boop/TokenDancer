from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import utcnow
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.order import Order
    from app.models.redeem import RedeemLog, RedeemCode
    from app.models.api_key import APIKey
    from app.models.usage import UsageRecord
    from app.models.account import BalanceLedger


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    role: Mapped[str] = mapped_column(String(20), default="user")  # 'user' | 'admin'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    # 账户余额（单位：美元）
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"))
    available_balance: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"))

    # Relationships
    carts: Mapped[list["Cart"]] = relationship("Cart", back_populates="user")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")
    redeem_logs: Mapped[list["RedeemLog"]] = relationship("RedeemLog", back_populates="user")
    redeem_codes: Mapped[list["RedeemCode"]] = relationship(
        "RedeemCode", back_populates="used_by_user"
    )
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user")
    usage_records: Mapped[list["UsageRecord"]] = relationship(
        "UsageRecord", back_populates="user"
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger", back_populates="user"
    )
