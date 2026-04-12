from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.core.config import settings


def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """Decode JWT and return payload. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def get_token_subject(token: str) -> int:
    """Extract user ID from JWT token. Raises JWTError if invalid."""
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise JWTError("Token missing 'sub' claim")
    return int(user_id)
