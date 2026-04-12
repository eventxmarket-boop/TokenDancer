import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.redeem import RedeemCode
from app.schemas.redeem_code import RedeemCodeCreate, RedeemCodeUpdate, RedeemCodeRead


def _generate_code(length: int = 12) -> str:
    """生成随机兑换码，格式：XXXX-XXXX-XXXX（字母数字）"""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    segments = []
    for _ in range(3):
        segment = "".join(secrets.choice(chars) for _ in range(4))
        segments.append(segment)
    return "-".join(segments)


class RedeemCodeService:
    def create(
        self,
        data: RedeemCodeCreate,
        db: Session,
    ) -> RedeemCodeRead:
        # 生成或使用提供的 code
        code = (data.code or _generate_code()).strip().upper()
        if len(code) < 4:
            raise ValueError("兑换码长度不能少于 4 位")

        # 检查是否已存在
        existing = db.query(RedeemCode).filter(RedeemCode.code == code).first()
        if existing:
            raise ValueError(f"兑换码 {code} 已存在，请换一个")

        reward_amount = Decimal(str(data.reward_amount))
        if reward_amount < 0:
            raise ValueError("奖励金额不能为负数")

        rc = RedeemCode(
            code=code,
            reward_type=data.reward_type or "balance",
            reward_amount=reward_amount,
            is_used=0,
            expires_at=data.expires_at,
        )
        db.add(rc)
        db.commit()
        db.refresh(rc)
        return RedeemCodeRead.model_validate(rc)

    def list_codes(
        self,
        db: Session,
        is_used: Optional[bool] = None,
        is_expired: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RedeemCodeRead]:
        q = db.query(RedeemCode)

        now = datetime.now(timezone.utc)

        if is_used is not None:
            q = q.filter(RedeemCode.is_used == (1 if is_used else 0))

        if is_expired is not None:
            if is_expired:
                q = q.filter(
                    or_(
                        RedeemCode.expires_at < now,
                        RedeemCode.is_used == 1,
                    )
                )
            else:
                q = q.filter(
                    RedeemCode.is_used == 0,
                    or_(
                        RedeemCode.expires_at.is_(None),
                        RedeemCode.expires_at >= now,
                    )
                )

        codes = (
            q.order_by(RedeemCode.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [RedeemCodeRead.model_validate(rc) for rc in codes]

    def update(self, code_id: int, data: RedeemCodeUpdate, db: Session) -> RedeemCodeRead | None:
        rc = db.query(RedeemCode).filter(RedeemCode.id == code_id).first()
        if not rc:
            return None
        if data.expires_at is not None:
            rc.expires_at = data.expires_at
        db.commit()
        db.refresh(rc)
        return RedeemCodeRead.model_validate(rc)

    def delete(self, code_id: int, db: Session) -> bool:
        rc = db.query(RedeemCode).filter(RedeemCode.id == code_id).first()
        if not rc:
            return False
        if rc.is_used:
            raise ValueError("已使用的兑换码无法删除")
        db.delete(rc)
        db.commit()
        return True


redeem_code_service = RedeemCodeService()
