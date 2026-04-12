from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_admin
from app.models.user import User
from app.schemas.route_policy import RoutePolicyCreate, RoutePolicyUpdate, RoutePolicyRead
from app.services.route_policy_service import route_policy_service

router = APIRouter(prefix="/admin/route-policies", tags=["admin-route-policies"])


@router.get("", response_model=list[RoutePolicyRead])
def list_route_policies(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return route_policy_service.list(db)


@router.post("", response_model=RoutePolicyRead)
def create_route_policy(
    data: RoutePolicyCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return route_policy_service.create(data, db)


@router.patch("/{policy_id}", response_model=RoutePolicyRead)
def update_route_policy(
    policy_id: int,
    data: RoutePolicyUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    p = route_policy_service.update(policy_id, data, db)
    if not p:
        raise HTTPException(status_code=404, detail="路由策略不存在")
    return p
