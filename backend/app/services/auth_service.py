from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserRead


class AuthService:
    # re-export for convenience (must use staticmethod so they don't become bound methods)
    verify_password = staticmethod(verify_password)  # noqa: N816
    hash_password = staticmethod(hash_password)      # noqa: N816

    def register(self, data: RegisterRequest, db: Session) -> User:
        # 检查唯一性
        existing = db.query(User).filter(
            (User.username == data.username) | (User.email == data.email)
        ).first()
        if existing:
            raise ValueError("Username or email already registered")
        user = User(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def login(self, data: LoginRequest, db: Session) -> TokenResponse:
        user = db.query(User).filter(User.email == data.email).first()
        if not user or not verify_password(data.password, user.password_hash):
            raise ValueError("Invalid email or password")
        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(
            access_token=token,
            user=UserRead.model_validate(user),
        )

    def after_login_success(self, email: str) -> None:
        """Call this after a successful login to clear failure counters."""
        from app.deps import _login_tracker
        _login_tracker.record_success(email)

    def get_me(self, user: User) -> UserRead:
        return UserRead.model_validate(user)


auth_service = AuthService()
