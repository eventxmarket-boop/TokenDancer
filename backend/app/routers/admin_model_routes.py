from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_admin, get_db
from app.models.user import User
from app.schemas.model_route import ModelRouteCreate, ModelRouteRead, ModelRouteUpdate
from app.services.model_route_service import model_route_service

router = APIRouter(prefix="/admin/model-routes", tags=["admin-model-routes"])


@router.get("", response_model=list[ModelRouteRead])
def list_model_routes(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return model_route_service.list_enriched(db)


@router.post("", response_model=ModelRouteRead)
def create_model_route(
    data: ModelRouteCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        route = model_route_service.create(data, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return model_route_service.serialize(route, db)


@router.patch("/{route_id}", response_model=ModelRouteRead)
def update_model_route(
    route_id: int,
    data: ModelRouteUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        route = model_route_service.update(route_id, data, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not route:
        raise HTTPException(status_code=404, detail="模型映射不存在")
    return model_route_service.serialize(route, db)
