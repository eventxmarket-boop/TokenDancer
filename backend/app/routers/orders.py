from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.order import OrderRead, OrderListItem
from app.services.order_service import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead)
def create_order(
    payment_method: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return order_service.create_from_cart(current_user.id, payment_method, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[OrderListItem])
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.list_orders(current_user.id, db)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = order_service.get_order(order_id, current_user.id, db)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order
