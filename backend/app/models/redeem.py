from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import utcnow
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class RedeemCode(Base):
    __tablename__ = "redeem_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    reward_type: Mapped[str] = mapped_column(String(20), default="balance")
    reward_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    is_used: Mapped[bool] = mapped_column(Integer, default=0)
    used_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    used_by_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="redeem_codes"
    )


class RedeemLog(Base):
    __tablename__ = "redeem_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="成功")
    message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    balance_delta: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="redeem_logs")
