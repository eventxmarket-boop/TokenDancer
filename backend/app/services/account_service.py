import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User
from app.models.account import BalanceLedger
from app.models.usage import UsageRecord
from app.schemas.account import UsageRecordCreate, UsageRecordRead, LedgerEntry, BalanceSnapshot


class AccountService:
    def get_balance(self, user_id: int, db: Session) -> BalanceSnapshot:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")
        return BalanceSnapshot(
            balance=round(float(user.balance), 4),
            available_balance=round(float(user.available_balance), 4),
        )

    def ledger_history(
        self,
        user_id: int,
        db: Session,
        limit: int = 50,
    ) -> list[LedgerEntry]:
        entries = (
            db.query(BalanceLedger)
            .filter(BalanceLedger.user_id == user_id)
            .order_by(desc(BalanceLedger.created_at))
            .limit(limit)
            .all()
        )
        return [LedgerEntry.model_validate(e) for e in entries]

    def list_ledger(self, user_id: int, db: Session, limit: int = 50) -> list[BalanceLedger]:
        """直接返回 BalanceLedger 列表（给 billing 路由用）"""
        return (
            db.query(BalanceLedger)
            .filter(BalanceLedger.user_id == user_id)
            .order_by(desc(BalanceLedger.created_at))
            .limit(limit)
            .all()
        )

    def get_or_create_account(self, user_id: int, db: Session):
        """返回用户账户（余额从 user.balance 读取）"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")
        return user

    # ---- Usage recording: creates usage record + deducts balance + writes ledger ----

    def record_usage(
        self,
        user_id: int,
        data: UsageRecordCreate,
        db: Session,
    ) -> UsageRecordRead:
        # 1. Fetch user and verify balance if deducting
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        cost = Decimal(str(data.cost))
        cost_amount = Decimal(str(data.cost_amount))
        balance_before = user.balance

        # 2. Create UsageRecord
        usage = UsageRecord(
            user_id=user_id,
            api_key_id=data.api_key_id,
            model_name=data.model_name,
            public_model_name=data.public_model_name,
            provider_id=data.provider_id,
            provider_key_id=data.provider_key_id,
            upstream_model_name=data.upstream_model_name,
            request_status=data.request_status,
            input_tokens=data.input_tokens,
            output_tokens=data.output_tokens,
            total_tokens=data.total_tokens,
            cost=cost,
            cost_amount=cost_amount,
            latency_ms=data.latency_ms,
            requested_at=datetime.now(timezone.utc),
        )
        db.add(usage)
        db.flush()  # get usage.id

        # 3. Deduct balance if flag is True
        if data.deduct_balance and cost > 0:
            if user.balance < cost:
                # Not enough balance — still record usage but flag balance insufficient
                user.balance = Decimal("0")
                user.available_balance = Decimal("0")
            else:
                user.balance -= cost
                user.available_balance = max(user.available_balance - cost, Decimal("0"))

            # 4. Write ledger entry
            ledger = BalanceLedger(
                user_id=user_id,
                operation="usage_debit",
                amount=-float(cost),  # negative for debit
                balance_before=float(balance_before),
                balance_after=float(user.balance),
                usage_record_id=usage.id,
                remark=f"API 使用扣费：{data.public_model_name or data.model_name}，tokens={data.total_tokens}",
            )
            db.add(ledger)

        db.commit()
        db.refresh(usage)
        return UsageRecordRead.model_validate(usage)

    # ---- Balance credit (called by redeem service) ----

    def credit_balance(
        self,
        user_id: int,
        amount: Decimal,
        db: Session,
        redeem_log_id: Optional[int] = None,
        order_id: Optional[int] = None,
        operation: str = "redeem_credit",
        remark: str = "",
    ) -> BalanceSnapshot:
        """增加用户余额，同时写 ledger。"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("充值金额必须为正数")

        balance_before = user.balance
        user.balance += amount
        user.available_balance += amount

        ledger = BalanceLedger(
            user_id=user_id,
            operation=operation,
            amount=float(amount),
            balance_before=float(balance_before),
            balance_after=float(user.balance),
            redeem_log_id=redeem_log_id,
            order_id=order_id,
            remark=remark,
        )
        db.add(ledger)
        db.commit()
        db.refresh(user)

        return BalanceSnapshot(
            balance=round(float(user.balance), 4),
            available_balance=round(float(user.available_balance), 4),
        )


account_service = AccountService()
