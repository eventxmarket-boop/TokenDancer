from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_admin, rate_limit_admin_mutation
from app.models.user import User
from app.schemas.admin_user import AdminUserRead, AdminUserUpdate
from app.schemas.admin_order import AdminOrderUpdate
from app.schemas.redeem_code import RedeemCodeCreate, RedeemCodeRead, RedeemCodeUpdate
from app.services.admin_user_service import admin_user_service
from app.services.admin_order_service import admin_order_service
from app.services.redeem_code_service import redeem_code_service
from app.services.admin_audit_service import admin_audit_service

router = APIRouter(prefix="/admin", tags=["admin"])


# ---- Admin: Users ----

@router.get("/users", response_model=list[AdminUserRead])
def admin_list_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """列出所有用户（仅 admin）。"""
    return admin_user_service.list_users(db)


@router.get("/users/{user_id}", response_model=AdminUserRead)
def admin_get_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取指定用户信息（仅 admin）。"""
    user = admin_user_service.get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.patch("/users/{user_id}", response_model=AdminUserRead)
def admin_update_user(
    user_id: int,
    data: AdminUserUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    更新指定用户：可修改 status / role / balance（仅 admin）。
    """
    rate_limit_admin_mutation(f"user.update:{current_admin.id}")
    # 读取 before_state
    before = admin_user_service.get_user(user_id, db)
    before_state = None
    if before:
        before_state = {
            "status": before.status,
            "role": before.role,
            "balance": str(before.balance),
        }

    user = admin_user_service.update_user(user_id, data, db)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 审计日志：记录变更字段
    after_state = {
        "status": data.status if data.status is not None else before.status if before else None,
        "role": data.role if data.role is not None else before.role if before else None,
        "balance": str(data.balance) if data.balance is not None else str(before.balance) if before else None,
    }
    admin_audit_service.log(
        db=db,
        action="user.update",
        admin_user_id=current_admin.id,
        target_type="user",
        target_id=str(user_id),
        before_state=before_state,
        after_state=after_state,
        ip_address=request.client.host if request else None,
    )
    return user


# ---- Admin: Orders ----

@router.get("/orders")
def admin_list_orders(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """列出所有订单（仅 admin）。"""
    return admin_order_service.list_orders(db)


@router.get("/orders/{order_id}")
def admin_get_order(
    order_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取订单详情（仅 admin）。"""
    order = admin_order_service.get_order(order_id, db)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.patch("/orders/{order_id}")
def admin_update_order(
    order_id: int,
    data: AdminOrderUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    更新订单状态（仅 admin）。
    """
    rate_limit_admin_mutation(f"order.update:{current_admin.id}")
    # 读取 before_state
    before = admin_order_service.get_order(order_id, db)
    before_state = None
    if before:
        before_state = {"status": before.status}

    order = admin_order_service.update_order(order_id, data, db)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    admin_audit_service.log(
        db=db,
        action="order.update",
        admin_user_id=current_admin.id,
        target_type="order",
        target_id=str(order_id),
        before_state=before_state,
        after_state={"status": order.status},
        ip_address=request.client.host if request else None,
    )
    return order


# ---- Admin: Redeem Codes ----

@router.post("/redeem-codes", response_model=RedeemCodeRead)
def admin_create_redeem_code(
    data: RedeemCodeCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """创建兑换码（仅 admin）。"""
    rate_limit_admin_mutation(f"redeem_code.create:{current_admin.id}")
    try:
        code = redeem_code_service.create(data, db)
        admin_audit_service.log(
            db=db,
            action="redeem_code.create",
            admin_user_id=current_admin.id,
            target_type="redeem_code",
            target_id=str(code.id),
            after_state={"code": code.code, "credits": str(code.credits)},
            ip_address=request.client.host if request else None,
        )
        return code
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/redeem-codes", response_model=list[RedeemCodeRead])
def admin_list_redeem_codes(
    is_used: bool | None = None,
    is_expired: bool | None = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """列出所有兑换码（仅 admin）。"""
    return redeem_code_service.list_codes(
        db, is_used=is_used, is_expired=is_expired, limit=500
    )


@router.patch("/redeem-codes/{code_id}", response_model=RedeemCodeRead)
def admin_update_redeem_code(
    code_id: int,
    data: RedeemCodeUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """更新兑换码（仅 admin）：可修改过期时间。"""
    rate_limit_admin_mutation(f"redeem_code.update:{current_admin.id}")
    before = redeem_code_service.get(code_id, db)
    before_state = None
    if before:
        before_state = {"expires_at": str(before.expires_at) if before.expires_at else None}

    code = redeem_code_service.update(code_id, data, db)
    if not code:
        raise HTTPException(status_code=404, detail="兑换码不存在")

    admin_audit_service.log(
        db=db,
        action="redeem_code.update",
        admin_user_id=current_admin.id,
        target_type="redeem_code",
        target_id=str(code_id),
        before_state=before_state,
        after_state={"expires_at": str(code.expires_at) if code.expires_at else None},
        ip_address=request.client.host if request else None,
    )
    return code


@router.delete("/redeem-codes/{code_id}")
def admin_delete_redeem_code(
    code_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """删除未使用的兑换码（仅 admin）。"""
    rate_limit_admin_mutation(f"redeem_code.delete:{current_admin.id}")
    # 读取 before_state
    before = redeem_code_service.get(code_id, db)
    before_state = None
    if before:
        before_state = {"code": before.code, "credits": str(before.credits)}

    try:
        ok = redeem_code_service.delete(code_id, db)
        if not ok:
            raise HTTPException(status_code=404, detail="兑换码不存在")

        admin_audit_service.log(
            db=db,
            action="redeem_code.delete",
            admin_user_id=current_admin.id,
            target_type="redeem_code",
            target_id=str(code_id),
            before_state=before_state,
            after_state=None,
            ip_address=request.client.host if request else None,
        )
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
