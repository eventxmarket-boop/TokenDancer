from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base_mixins import utcnow
from app.core.database import Base


class AdminAuditLog(Base):
    """
    管理员操作审计日志。
    记录高风险操作的管理员行为。
    """
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    # "provider_key.create" | "provider_key.update" | "user.role_change" | "order.status_change" 等
    target_type: Mapped[str] = mapped_column(String(50), nullable=True)
    # "provider_key" | "user" | "order" | "redeem_code" | "route_policy"
    target_id: Mapped[str] = mapped_column(String(100), nullable=True)
    before_state: Mapped[str] = mapped_column(Text, nullable=True)
    after_state: Mapped[str] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
