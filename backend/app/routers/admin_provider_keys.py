from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.deps import get_current_admin, get_db, rate_limit_admin_mutation
from app.models.user import User
from app.schemas.provider_key import ProviderKeyCreate, ProviderKeyRead, ProviderKeyUpdate
from app.services.admin_audit_service import admin_audit_service
from app.services.provider_key_service import provider_key_service

router = APIRouter(prefix="/admin/provider-keys", tags=["admin-provider-keys"])


@router.get("", response_model=list[ProviderKeyRead])
def list_provider_keys(
    provider_id: int | None = None,
    status: str | None = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return provider_key_service.list_enriched(db, provider_id=provider_id, status=status)


@router.get("/{key_id}", response_model=ProviderKeyRead)
def get_provider_key(
    key_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    key = provider_key_service.get_enriched(key_id, db)
    if not key:
        raise HTTPException(status_code=404, detail="Key 不存在")
    return key


@router.post("", response_model=ProviderKeyRead)
def create_provider_key(
    data: ProviderKeyCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    rate_limit_admin_mutation(f"provider_key.create:{current_admin.id}")
    try:
        key = provider_key_service.create(data, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    admin_audit_service.log(
        db=db,
        action="provider_key.create",
        admin_user_id=current_admin.id,
        target_type="provider_key",
        target_id=str(key.id),
        after_state={"provider_id": key.provider_id, "key_masked": key.key_masked},
        ip_address=request.client.host if request else None,
    )
    return provider_key_service.serialize(key, db)


@router.patch("/{key_id}", response_model=ProviderKeyRead)
def update_provider_key(
    key_id: int,
    data: ProviderKeyUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    rate_limit_admin_mutation(f"provider_key.update:{current_admin.id}")
    before = provider_key_service.get(key_id, db)
    before_state = None
    if before:
        before_state = {
            "status": before.status,
            "provider_id": before.provider_id,
            "key_masked": before.key_masked,
        }

    try:
        key = provider_key_service.update(key_id, data, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not key:
        raise HTTPException(status_code=404, detail="Key 不存在")

    admin_audit_service.log(
        db=db,
        action="provider_key.update",
        admin_user_id=current_admin.id,
        target_type="provider_key",
        target_id=str(key.id),
        before_state=before_state,
        after_state={"status": key.status, "provider_id": key.provider_id, "key_masked": key.key_masked},
        ip_address=request.client.host if request else None,
    )
    return provider_key_service.serialize(key, db)


@router.delete("/{key_id}")
def delete_provider_key(
    key_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    rate_limit_admin_mutation(f"provider_key.delete:{current_admin.id}")
    before = provider_key_service.get(key_id, db)
    before_state = None
    if before:
        before_state = {"status": before.status, "provider_id": before.provider_id, "key_masked": before.key_masked}

    ok = provider_key_service.delete(key_id, db)
    if not ok:
        raise HTTPException(status_code=404, detail="Key 不存在")

    admin_audit_service.log(
        db=db,
        action="provider_key.delete",
        admin_user_id=current_admin.id,
        target_type="provider_key",
        target_id=str(key_id),
        before_state=before_state,
        after_state=None,
        ip_address=request.client.host if request else None,
    )
    return {"ok": True}
