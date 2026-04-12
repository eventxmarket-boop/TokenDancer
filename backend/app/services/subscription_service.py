from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.subscription import Subscription
from app.models.token_grant import TokenGrant
from app.schemas.subscription import SubscriptionRead, TokenGrantRead


class SubscriptionService:
    def list_user_subscriptions(self, user_id: int, db: Session) -> list[SubscriptionRead]:
        subs = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).all()
        return [SubscriptionRead.model_validate(s) for s in subs]

    def get_active(self, user_id: int, db: Session) -> SubscriptionRead | None:
        now = datetime.now(timezone.utc)
        sub = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "active",
            Subscription.expires_at > now,
        ).first()
        if not sub:
            return None
        return SubscriptionRead.model_validate(sub)

    def create_subscription(
        self,
        user_id: int,
        plan_name: str,
        days: int,
        db: Session,
        product_id: int | None = None,
        order_id: int | None = None,
    ) -> SubscriptionRead:
        now = datetime.now(timezone.utc)
        # 检查是否已有 active 订阅：简单覆盖策略
        existing = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "active",
        ).first()
        if existing:
            # 顺延策略：把旧的 expires_at 作为新的 starts_at
            starts_at = existing.expires_at
            existing.status = "replaced"
        else:
            starts_at = now

        expires_at = starts_at + timedelta(days=days)
        sub = Subscription(
            user_id=user_id,
            product_id=product_id,
            plan_name=plan_name,
            status="active",
            starts_at=starts_at,
            expires_at=expires_at,
            source_order_id=order_id,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return SubscriptionRead.model_validate(sub)

    def list_user_token_grants(self, user_id: int, db: Session) -> list[TokenGrantRead]:
        grants = db.query(TokenGrant).filter(
            TokenGrant.user_id == user_id,
        ).order_by(TokenGrant.created_at.desc()).all()
        return [TokenGrantRead.model_validate(g) for g in grants]

    def create_token_grant(
        self,
        user_id: int,
        quota: int,
        db: Session,
        product_id: int | None = None,
        order_id: int | None = None,
        expires_at=None,
    ) -> TokenGrantRead:
        grant = TokenGrant(
            user_id=user_id,
            product_id=product_id,
            quota=quota,
            used=0,
            status="active",
            source_order_id=order_id,
            expires_at=expires_at,
        )
        db.add(grant)
        db.commit()
        db.refresh(grant)
        return TokenGrantRead.model_validate(grant)


subscription_service = SubscriptionService()
