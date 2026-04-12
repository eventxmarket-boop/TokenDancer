from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.healthcheck import sync_check_provider_health
from app.deps import get_current_admin, get_db
from app.models.provider import Provider
from app.models.user import User
from app.schemas.provider import ProviderCreate, ProviderRead, ProviderUpdate
from app.services.provider_service import provider_service

router = APIRouter(prefix="/admin/providers", tags=["admin-providers"])


@router.get("", response_model=list[ProviderRead])
def list_providers(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return provider_service.list_enriched(db)


@router.get("/{provider_id}", response_model=ProviderRead)
def get_provider(
    provider_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    provider = provider_service.get_enriched(provider_id, db)
    if not provider:
        raise HTTPException(status_code=404, detail="渠道不存在")
    return provider


@router.post("", response_model=ProviderRead)
def create_provider(
    data: ProviderCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        provider = provider_service.create(data, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return provider_service.serialize(provider, db)


@router.patch("/{provider_id}", response_model=ProviderRead)
def update_provider(
    provider_id: int,
    data: ProviderUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        provider = provider_service.update(provider_id, data, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not provider:
        raise HTTPException(status_code=404, detail="渠道不存在")
    return provider_service.serialize(provider, db)


@router.post("/{provider_id}/health-check")
def health_check_provider(
    provider_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="渠道不存在")

    old_status = provider.health_status
    new_status = sync_check_provider_health(provider)

    provider.health_status = new_status
    provider.last_health_check_at = datetime.utcnow()
    db.commit()

    return {
        "id": provider.id,
        "name": provider.name,
        "old_status": old_status,
        "new_status": new_status,
    }


@router.post("/health-check-all")
def health_check_all(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    providers = db.query(Provider).filter(Provider.is_active == True).all()
    results = []
    for provider in providers:
        old = provider.health_status
        new = sync_check_provider_health(provider)
        provider.health_status = new
        provider.last_health_check_at = datetime.utcnow()
        results.append({"id": provider.id, "name": provider.name, "old": old, "new": new})
    db.commit()
    return {"total": len(results), "providers": results}
