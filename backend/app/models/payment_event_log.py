from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base_mixins import utcnow
from app.core.database import Base


class PaymentEventLog(Base):
    """
    支付事件日志（webhook callback 记录）。
    用于幂等保护、问题排查、审计追踪。
    """
    __tablename__ = "payment_event_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    # 上游支付事件唯一ID，用于幂等
    provider: Mapped[str] = mapped_column(String(50), nullable=True)
    # "stripe" | "alipay" | "wxpay" | "custom"
    order_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    payment_id: Mapped[str] = mapped_column(String(100), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # "payment_intent.succeeded" | "payment_intent.failed" | "checkout.session.completed"
    verify_result: Mapped[str] = mapped_column(String(20), nullable=True)
    # "passed" | "failed" | "missing_secret"
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_result: Mapped[str] = mapped_column(String(50), nullable=True)
    # "fulfilled" | "already_paid" | "order_not_found" | "error"
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
