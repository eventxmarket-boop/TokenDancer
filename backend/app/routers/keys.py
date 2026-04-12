from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.api_key import APIKeyCreate, APIKeyRead, APIKeyUpdate
from app.services.key_service import key_service

router = APIRouter(prefix="/keys", tags=["keys"])


@router.get("/available-models")
def list_available_models(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    models = key_service.get_available_models(db)
    return {"models": models, "can_create": bool(models)}


@router.get("", response_model=list[APIKeyRead])
def list_keys(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return key_service.list_keys(current_user.id, db)


@router.post("", response_model=APIKeyRead)
def create_key(data: APIKeyCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return key_service.create_key(current_user.id, data, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{key_id}", response_model=APIKeyRead)
def update_key(
    key_id: int,
    data: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result, err = key_service.update_key(key_id, current_user.id, data, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Key not found")
    if err:
        raise HTTPException(status_code=400, detail=err)
    return result


@router.delete("/{key_id}")
def delete_key(key_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ok = key_service.delete_key(key_id, current_user.id, db)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"ok": True}
