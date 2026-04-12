from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import utcnow
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.provider_key import ProviderKey


class Provider(Base):
    """
    上游 API 渠道/线路。
    例如：OpenAI、Anthropic、某代理服务等。
    """
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # provider_type 示例: openai | anthropic | gemini | proxy | custom
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    health_status: Mapped[str] = mapped_column(String(20), default="unknown")
    # health_status: unknown | healthy | degraded | down
    last_health_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    keys: Mapped[list["ProviderKey"]] = relationship("ProviderKey", back_populates="provider")
