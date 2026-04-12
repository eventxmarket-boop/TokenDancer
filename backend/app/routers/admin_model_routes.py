from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_admin
from app.models.user import User
from app.schemas.model_route import ModelRouteCreate, ModelRouteUpdate, ModelRouteRead
from app.services.model_route_service import model_route_service

router = APIRouter(prefix="/admin/model-routes", tags=["admin-model-routes"])


@router.get("", response_model=list[ModelRouteRead])
def list_model_routes(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return model_route_service.list_routes(db)


@router.post("", response_model=ModelRouteRead)
def create_model_route(
    data: ModelRouteCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        return model_route_service.create(data, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{route_id}", response_model=ModelRouteRead)
def update_model_route(
    route_id: int,
    data: ModelRouteUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        r = model_route_service.update(route_id, data, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not r:
        raise HTTPException(status_code=404, detail="模型映射不存在")
    return r
