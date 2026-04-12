from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Numeric, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_mixins import utcnow
from app.core.database import Base


class ModelRoute(Base):
    """
    模型映射：public_model_name → provider_model_name
    例如：gpt-4o → gpt-4o-2024-08-06
    """
    __tablename__ = "model_routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 用户请求时用的模型名
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), nullable=False)
    # 对应的上游 Provider
    provider_model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 上游真实模型名
    fallback_provider_id: Mapped[Optional[int]] = mapped_column(ForeignKey("providers.id"), nullable=True)
    fallback_model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # 备用上游（可选）
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    cost_multiplier: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0)
    max_context: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
