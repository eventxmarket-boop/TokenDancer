from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models.user import User
from app.services.profile_service import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    username: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.get("")
def get_profile(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户个人资料。"""
    return profile_service.get_profile(current_user)


@router.put("")
def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新个人资料（目前支持修改用户名）。"""
    try:
        return profile_service.update_profile(
            current_user, {"username": data.username}, db
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/password")
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码。"""
    try:
        return profile_service.change_password(
            current_user, data.current_password, data.new_password, db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
