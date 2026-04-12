from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user, rate_limit
from app.core.config import settings
from app.models.user import User
from app.schemas.redeem import RedeemRequest, RedeemResponse, RedeemLogRead
from app.services.redeem_service import redeem_service

router = APIRouter(prefix="/redeem", tags=["redeem"])


@router.post("", response_model=RedeemResponse)
def redeem(
    data: RedeemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """兑换码兑换（限流保护）。"""
    rate_limit(f"redeem:{current_user.id}", settings.RATE_LIMIT_REDEEM)
    return redeem_service.redeem(data.code, current_user, db)


@router.get("/history", response_model=list[RedeemLogRead])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return redeem_service.get_history(current_user.id, db)
