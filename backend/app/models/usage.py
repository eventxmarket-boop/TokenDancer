from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import utcnow
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.api_key import APIKey


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    api_key_id: Mapped[int] = mapped_column(ForeignKey("api_keys.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    public_model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    provider_id: Mapped[Optional[int]] = mapped_column(ForeignKey("providers.id"), nullable=True)
    provider_key_id: Mapped[Optional[int]] = mapped_column(ForeignKey("provider_keys.id"), nullable=True)
    upstream_model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    request_status: Mapped[str] = mapped_column(String(20), default="success")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=Decimal("0"))
    cost_amount: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=Decimal("0"))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="usage_records")
    api_key: Mapped["APIKey"] = relationship("APIKey")
