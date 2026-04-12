from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.cart import CartRead, CartItemCreate, CartItemUpdate, CouponUpdate
from app.services.cart_service import cart_service

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartRead)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = cart_service.get_cart(current_user.id, db)
    if not cart:
        return cart_service.get_or_create_cart(current_user.id, db)
    return cart


@router.post("/items", response_model=CartRead)
def add_cart_item(
    data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return cart_service.add_item(current_user.id, data, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/items/{item_id}", response_model=CartRead)
def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return cart_service.update_item(current_user.id, item_id, data, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/items/{item_id}", response_model=CartRead)
def delete_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return cart_service.delete_item(current_user.id, item_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/coupon", response_model=CartRead)
def set_coupon(
    data: CouponUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_service.set_coupon(current_user.id, data.coupon_code, db)
