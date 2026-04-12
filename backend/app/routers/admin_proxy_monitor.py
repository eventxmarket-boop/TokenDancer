from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.deps import get_current_admin, get_db
from app.models.user import User
from app.services.proxy_gateway_service import proxy_gateway_service
from app.services.proxy_monitor_service import proxy_monitor_service

router = APIRouter(prefix="/admin/proxy-monitor", tags=["admin-proxy-monitor"])


@router.get("/overview")
def overview(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return proxy_monitor_service.overview(db)


@router.get("/providers")
def providers(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return proxy_monitor_service.providers(db)


@router.get("/models")
def models(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return proxy_monitor_service.models(db)


@router.get("/failures")
def failures(
    limit: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return proxy_monitor_service.failures(db, limit=limit)


@router.post("/providers/{provider_id}/probe")
async def probe_provider(
    provider_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        return await proxy_gateway_service.probe_provider(provider_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/models/{route_id}/switch")
def switch_model_route(
    route_id: int,
    payload: dict = Body(default={}),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        return proxy_monitor_service.switch_route(route_id, db, mode=payload.get("mode", "swap"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
