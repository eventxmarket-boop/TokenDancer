from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models.user import User
from app.services.subscription_service import subscription_service
from app.services.account_service import account_service
from app.schemas.subscription import SubscriptionRead, TokenGrantRead

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/me", response_model=list[SubscriptionRead])
def get_my_subscriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的订阅列表"""
    return subscription_service.list_user_subscriptions(current_user.id, db)


@router.get("/me/active", response_model=SubscriptionRead | None)
def get_my_active_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户生效中的订阅"""
    return subscription_service.get_active(current_user.id, db)


@router.get("/me/token-grants", response_model=list[TokenGrantRead])
def get_my_token_grants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的 Token 配额列表"""
    return subscription_service.list_user_token_grants(current_user.id, db)
