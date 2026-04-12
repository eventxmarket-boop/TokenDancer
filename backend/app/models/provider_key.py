from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import utcnow
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.provider import Provider


class ProviderKey(Base):
    """
    上游 API Key 池。
    - key_masked: 前端展示用（脱敏）
    - key_encrypted: 加密存储的真实 key
    """
    __tablename__ = "provider_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 脱敏显示值，如 sk-abc1****xyz9
    key_masked: Mapped[str] = mapped_column(String(100), nullable=False)
    # 加密存储的真实 key
    key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    # 该 key 支持的模型列表，逗号分隔
    supported_models: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    # status: active | disabled | invalid
    weight: Mapped[int] = mapped_column(Integer, default=1)
    rpm_limit: Mapped[int] = mapped_column(Integer, default=1000)
    daily_limit: Mapped[int] = mapped_column(Integer, default=100000)
    used_count_today: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    provider: Mapped["Provider"] = relationship("Provider", back_populates="keys")
