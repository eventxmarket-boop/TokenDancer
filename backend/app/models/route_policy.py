from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_mixins import utcnow
from app.core.database import Base


class RoutePolicy(Base):
    """
    路由策略：决定某个模型请求走哪条线路、失败怎么切换。
    policy_type: fixed | weighted | fallback | cost_first
    """
    __tablename__ = "route_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    public_model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    primary_provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), nullable=False)
    secondary_provider_id: Mapped[Optional[int]] = mapped_column(ForeignKey("providers.id"), nullable=True)
    policy_type: Mapped[str] = mapped_column(String(30), default="fixed")
    # fixed: 固定走 primary
    # weighted: 按 weight 分配（需要配合 ProviderKey.weight）
    # fallback: primary 失败自动切换 secondary
    # cost_first: 优先选 cost_multiplier 最低的
    retry_count: Mapped[int] = mapped_column(Integer, default=1)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=60)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
