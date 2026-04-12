from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.redeem import RedeemCode, RedeemLog
from app.models.user import User
from app.schemas.redeem import RedeemRequest, RedeemResponse, RedeemLogRead
from app.services.account_service import account_service


class RedeemService:
    def redeem(self, code: str, user: User, db: Session) -> RedeemResponse:
        # 清洗输入
        code = code.strip().upper()

        redeem_code = db.query(RedeemCode).filter(RedeemCode.code == code).first()

        # 状态1：不存在
        if not redeem_code:
            self._write_log(db, user.id, code, "失败", "兑换码不存在", Decimal("0"))
            return RedeemResponse(success=False, message="兑换码不存在", balance_delta=0.0)

        # 状态2：已过期
        now = datetime.now(timezone.utc)
        if redeem_code.expires_at and redeem_code.expires_at < now:
            self._write_log(db, user.id, code, "失败", "兑换码已过期", Decimal("0"))
            return RedeemResponse(success=False, message="兑换码已过期", balance_delta=0.0)

        # 状态3：已使用
        if redeem_code.is_used:
            self._write_log(db, user.id, code, "失败", "兑换码已被使用", Decimal("0"))
            return RedeemResponse(success=False, message="兑换码已被使用", balance_delta=0.0)

        # 状态4：成功兑换
        redeem_code.is_used = 1
        redeem_code.used_by = user.id
        redeem_code.used_at = now
        db.flush()  # get redeem_code.id before commit

        amount = Decimal(str(redeem_code.reward_amount))

        # 写 RedeemLog（历史记录保留）
        redeem_log = RedeemLog(
            user_id=user.id,
            code=code,
            status="成功",
            message=f"兑换成功，获得 ${redeem_code.reward_amount}",
            balance_delta=amount,
        )
        db.add(redeem_log)
        db.flush()

        # 真实更新用户余额 + 写 ledger
        if redeem_code.reward_type == "balance" and amount > 0:
            account_service.credit_balance(
                user_id=user.id,
                amount=amount,
                db=db,
                redeem_log_id=redeem_log.id,
                remark=f"兑换码充值：{code}",
            )

        db.commit()

        return RedeemResponse(
            success=True,
            message=f"兑换成功，获得 ${redeem_code.reward_amount}",
            balance_delta=float(amount),
        )

    def _write_log(
        self, db: Session, user_id: int, code: str,
        status: str, message: str, balance_delta: Decimal,
    ):
        log = RedeemLog(
            user_id=user_id,
            code=code,
            status=status,
            message=message,
            balance_delta=balance_delta,
        )
        db.add(log)
        db.commit()

    def get_history(self, user_id: int, db: Session) -> list[RedeemLogRead]:
        logs = (
            db.query(RedeemLog)
            .filter(RedeemLog.user_id == user_id)
            .order_by(RedeemLog.created_at.desc())
            .all()
        )
        return [RedeemLogRead.model_validate(log) for log in logs]


redeem_service = RedeemService()
