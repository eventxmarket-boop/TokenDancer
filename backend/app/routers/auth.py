import re
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user, rate_limit, check_login_cooldown
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserRead
from app.schemas.profile import ProfileRead, ProfileUpdate, PasswordChange
from app.services.auth_service import auth_service
from app.services.email_service import email_service
from app.core.logging import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)

# ---- Password policy ----
PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$")
WEAK_PASSWORDS = {
    "password", "password123", "password1234", "12345678", "123456789",
    "qwerty", "abc123", "admin123", "letmein", "welcome",
}


def _validate_password(password: str) -> None:
    """Validate password strength. Raises HTTPException if invalid."""
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(status_code=422, detail=f"密码长度不能少于 {PASSWORD_MIN_LENGTH} 位")
    if not PASSWORD_PATTERN.match(password):
        raise HTTPException(
            status_code=422,
            detail="密码必须包含大小写字母和数字"
        )
    if password.lower() in WEAK_PASSWORDS:
        raise HTTPException(status_code=422, detail="密码太弱，请换一个更安全的密码")


# ---- Auth routes ----

@router.post("/register", response_model=UserRead)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册（限流 + 密码强度校验）。"""
    rate_limit(f"register:{data.email}", settings.RATE_LIMIT_REGISTER)

    try:
        _validate_password(data.password)
    except HTTPException:
        raise

    try:
        user = auth_service.register(data, db)
        logger.info(f"New user registered: {user.email}")
        try:
            email_service.send_welcome(user.email, user.username)
        except Exception as e:
            logger.warning(f"Welcome email failed: {e}")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """用户登录（限流 + 登录失败冷却）。"""
    rate_limit(f"login:{data.email}", settings.RATE_LIMIT_LOGIN)
    check_login_cooldown(data.email)

    try:
        result = auth_service.login(data, db)
        auth_service.after_login_success(data.email)
        logger.info(f"User logged in: {data.email}")
        return result
    except ValueError as e:
        from app.deps import _login_tracker
        _login_tracker.record_failure(data.email)
        logger.warning(f"Failed login for {data.email}")
        # Always return same message to avoid email enumeration
        raise HTTPException(status_code=401, detail="邮箱或密码错误")


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ---- Profile ----

@router.get("/profile", response_model=ProfileRead)
def get_profile(current_user: User = Depends(get_current_user)):
    return ProfileRead.model_validate(current_user)


@router.put("/profile", response_model=ProfileRead)
def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.username is not None:
        if len(data.username.strip()) < 2:
            raise HTTPException(status_code=422, detail="用户名不能少于 2 个字符")
        current_user.username = data.username.strip()
    db.commit()
    db.refresh(current_user)
    return ProfileRead.model_validate(current_user)


@router.put("/password")
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码（限流 + 密码强度校验）。"""
    rate_limit(f"password:{current_user.id}", settings.RATE_LIMIT_PASSWORD)

    if not auth_service.verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码不正确")

    try:
        _validate_password(data.new_password)
    except HTTPException:
        raise

    current_user.password_hash = auth_service.hash_password(data.new_password)
    db.commit()
    logger.info(f"Password changed for: {current_user.email}")

    try:
        email_service.send_password_changed(current_user.email, current_user.username)
    except Exception as e:
        logger.warning(f"Password change email failed: {e}")

    return {"ok": True, "message": "密码修改成功"}

# ---- Forgot Password ----

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """发送密码重置邮件（已注册用户）。"""
    from app.services.auth_service import auth_service
    user = auth_service.get_user_by_email(data.email, db)
    if user is None:
        # 不暴露用户是否存在，统一返回成功
        logger.info(f"Forgot password requested for non-existent email: {data.email}")
        return {"ok": True, "message": "如果该邮箱已注册，重置链接已发送"}
    try:
        email_service.send_password_reset(user.email, user.username)
        logger.info(f"Password reset email sent to: {user.email}")
    except Exception as e:
        logger.warning(f"Password reset email failed for {user.email}: {e}")
        return {"ok": True, "message": "如果该邮箱已注册，重置链接已发送"}
    return {"ok": True, "message": "如果该邮箱已注册，重置链接已发送"}
