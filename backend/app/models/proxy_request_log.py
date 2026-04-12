from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_mixins import utcnow
from app.core.database import Base


class ProxyRequestLog(Base):
    """
    API 中转请求日志。
    记录每条请求的路由、状态、tokens、cost、延迟。
    """
    __tablename__ = "proxy_request_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # 外部请求 ID，便于追踪
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    user_api_key_id: Mapped[Optional[int]] = mapped_column(ForeignKey("api_keys.id"), nullable=True)
    public_model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_id: Mapped[Optional[int]] = mapped_column(ForeignKey("providers.id"), nullable=True)
    provider_key_id: Mapped[Optional[int]] = mapped_column(ForeignKey("provider_keys.id"), nullable=True)
    provider_model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    request_status: Mapped[str] = mapped_column(String(20), default="success")
    # success | error | timeout | rate_limited
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # 扩展字段
    upstream_provider_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    upstream_key_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    request_origin: Mapped[str] = mapped_column(String(30), default="proxy")
    request_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    policy_type: Mapped[str] = mapped_column(String(30), default="fixed")
    fallback_triggered: Mapped[bool] = mapped_column(default=False)
    retry_attempt: Mapped[int] = mapped_column(Integer, default=0)
    # v4.0.0 扩展字段
    provider_switch_count: Mapped[int] = mapped_column(Integer, default=0)
    key_switch_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_chain_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
