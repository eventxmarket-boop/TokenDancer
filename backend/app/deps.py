from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session
import time

from app.core.config import settings
from app.core.security import get_token_subject
from app.core.database import SessionLocal
from app.models.api_key import APIKey
from app.models.user import User
from app.services.key_service import key_service

security = HTTPBearer(auto_error=False)


@dataclass
class ProxyAuthContext:
    user: User
    api_key: APIKey | None = None

    @property
    def user_id(self) -> int:
        return self.user.id

    @property
    def api_key_id(self) -> int | None:
        return self.api_key.id if self.api_key else None

    @property
    def allowed_models(self) -> set[str] | None:
        raw = (self.api_key.allowed_models or "").strip() if self.api_key else ""
        if not raw:
            return None
        return {model.strip() for model in raw.split(",") if model.strip()}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---- Rate limiter ----

class RateLimiter:
    """Simple in-memory sliding-window rate limiter."""

    def __init__(self):
        self._hits: dict[str, list[float]] = {}

    def check(self, key: str, limit: int, window: int = 60) -> bool:
        now = time.time()
        window_start = now - window
        if key not in self._hits:
            self._hits[key] = []
        self._hits[key] = [t for t in self._hits[key] if t > window_start]
        if len(self._hits[key]) >= limit:
            return False
        self._hits[key].append(now)
        return True


_rate_limiter = RateLimiter()


def rate_limit(key: str, limit: int, window: int = 60):
    """Dependency. Raises 429 if rate limit exceeded."""
    if not settings.RATE_LIMIT_ENABLED:
        return
    if not _rate_limiter.check(key, limit, window):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
        )


def rate_limit_admin_mutation(key: str):
    """Admin 高风险操作限流，每分钟 30 次。"""
    rate_limit(f"admin_mut:{key}", settings.RATE_LIMIT_ADMIN_MUTATION)


# ---- Login failure tracker ----

class LoginFailureTracker:
    """
    Tracks consecutive failed login attempts per email.
    After LOGIN_MAX_FAILURES failures, the account is locked for LOGIN_COOLDOWN_SECONDS.
    """

    def __init__(self):
        # email → (consecutive_failures, last_failure_timestamp)
        self._failures: dict[str, tuple[int, float]] = {}
        # email → unlock_after timestamp (if locked)
        self._locks: dict[str, float] = {}

    def record_failure(self, email: str) -> None:
        now = time.time()
        prev = self._failures.get(email, (0, 0))[0]
        self._failures[email] = (prev + 1, now)
        # Trigger lockout if max failures reached
        if prev + 1 >= settings.LOGIN_MAX_FAILURES:
            self._locks[email] = now + settings.LOGIN_COOLDOWN_SECONDS

    def record_success(self, email: str) -> None:
        self._failures.pop(email, None)
        self._locks.pop(email, None)

    def is_locked(self, email: str) -> bool:
        if email not in self._locks:
            return False
        now = time.time()
        if now >= self._locks[email]:
            # Lock expired
            self._locks.pop(email, None)
            self._failures.pop(email, None)
            return False
        return True

    def lockout_remaining_seconds(self, email: str) -> int:
        if email not in self._locks:
            return 0
        remaining = self._locks[email] - time.time()
        return int(remaining) if remaining > 0 else 0


_login_tracker = LoginFailureTracker()


def check_login_cooldown(email: str) -> None:
    """Dependency. Raises 429 if account is locked from repeated failures."""
    if not settings.LOGIN_COOLDOWN_ENABLED:
        return
    if _login_tracker.is_locked(email):
        remaining = _login_tracker.lockout_remaining_seconds(email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录失败次数过多，请在 {remaining} 秒后重试",
        )


# ---- Auth dependencies ----

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _get_user_from_jwt(credentials.credentials, db)


def _get_user_from_jwt(token: str, db: Session) -> User:
    try:
        user_id = get_token_subject(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用",
        )

    return user


def _validate_api_key_for_proxy(api_key: APIKey, db: Session) -> ProxyAuthContext:
    if api_key.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="平台 API Key 已停用",
        )

    now = datetime.now(timezone.utc)
    expires_at = api_key.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="平台 API Key 已过期",
        )

    user = db.query(User).filter(User.id == api_key.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key 所属用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key 所属账户已被禁用",
        )

    return ProxyAuthContext(user=user, api_key=api_key)


def get_proxy_auth_context(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> ProxyAuthContext:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少中转认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    api_key = key_service.get_by_key_value(token, db)
    if api_key is not None:
        return _validate_api_key_for_proxy(api_key, db)

    user = _get_user_from_jwt(token, db)
    return ProxyAuthContext(user=user, api_key=None)


def ensure_proxy_model_access(auth: ProxyAuthContext, public_model: str) -> None:
    allowed_models = auth.allowed_models
    if allowed_models is not None and public_model not in allowed_models:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"当前平台 API Key 无权访问模型 {public_model}",
        )


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user
