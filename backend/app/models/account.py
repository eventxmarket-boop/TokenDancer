from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, ForeignKey, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import utcnow
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class BalanceLedger(Base):
    """
    余额流水/账本。
    所有余额变化（充值/兑换/消费/人工调整）均写入此表。
    通过 balance_after 可实时重建任意时刻余额。
    """
    __tablename__ = "balance_ledger"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    operation: Mapped[str] = mapped_column(String(30), nullable=False)
    # operation 类型:
    #   redeem_credit  - 兑换码充值
    #   usage_debit     - API 使用扣费
    #   manual_credit  - 人工增加（预留）
    #   manual_debit   - 人工扣减（预留）
    #   order_refund    - 订单退款（预留）

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    # amount: 正数表示增加，负数表示减少（统一在 service 层处理符号）

    balance_before: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"))
    balance_after: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"))

    # 可选关联
    redeem_log_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    usage_record_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    order_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("ix_balance_ledger_user_created", "user_id", "created_at"),
        Index("ix_balance_ledger_operation", "operation"),
    )
