from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.saved_item import SavedItemBatchReplaceRequest, SavedItemRead
from app.services.saved_item_service import clear_saved_items, list_saved_items, replace_saved_items

router = APIRouter()


@router.get("/persona-api/saved-items/{kind}", response_model=list[SavedItemRead])
def get_saved_items(
    kind: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_saved_items(db, current_user.id, kind)


@router.put("/persona-api/saved-items/{kind}", response_model=list[SavedItemRead])
def replace_items(
    kind: str,
    payload: SavedItemBatchReplaceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return replace_saved_items(db, current_user.id, kind, payload.items)


@router.delete("/persona-api/saved-items/{kind}")
def delete_items(
    kind: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clear_saved_items(db, current_user.id, kind)
    return {"ok": True}
