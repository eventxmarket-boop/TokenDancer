import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.constants import KEY_STATUS_ACTIVE, VALID_KEY_STATUSES
from app.models.api_key import APIKey
from app.models.model_route import ModelRoute
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate


def generate_key() -> str:
    return secrets.token_urlsafe(32)


class KeyService:
    @staticmethod
    def _normalize_dt(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    @staticmethod
    def _available_models(db: Session) -> list[str]:
        rows = (
            db.query(ModelRoute.public_model_name)
            .filter(ModelRoute.is_active == True)
            .distinct()
            .order_by(ModelRoute.public_model_name.asc())
            .all()
        )
        return [row[0] for row in rows if row and row[0]]

    def list_keys(self, user_id: int, db: Session) -> list[APIKey]:
        return db.query(APIKey).filter(APIKey.user_id == user_id).order_by(APIKey.created_at.desc()).all()

    def get_available_models(self, db: Session) -> list[str]:
        return self._available_models(db)

    def _normalize_allowed_models(self, allowed_models: str | None, db: Session) -> str | None:
        if allowed_models is None:
            return None
        models = [item.strip() for item in allowed_models.split(",") if item.strip()]
        if not models:
            return None
        available = set(self._available_models(db))
        if not available:
            raise ValueError("当前暂无可用 Model Route，请先完成后台 Provider -> Provider Key -> Model Route 配置")
        invalid = [item for item in models if item not in available]
        if invalid:
            raise ValueError(f"以下模型尚未配置可用路由: {', '.join(invalid)}")
        return ", ".join(dict.fromkeys(models))

    def create_key(self, user_id: int, data: APIKeyCreate, db: Session) -> APIKey:
        available = self._available_models(db)
        if not available:
            raise ValueError("当前暂无可用 Model Route，请联系管理员先完成 Provider -> Provider Key -> Model Route 配置")
        key = APIKey(
            user_id=user_id,
            name=data.name.strip(),
            key_value=generate_key(),
            group_name=(data.group_name or "default").strip() or "default",
            status=KEY_STATUS_ACTIVE,
            allowed_models=self._normalize_allowed_models(data.allowed_models, db),
            expires_at=data.expires_at,
        )
        db.add(key)
        db.commit()
        db.refresh(key)
        return key

    def update_key(self, key_id: int, user_id: int, data: APIKeyUpdate, db: Session) -> tuple[APIKey | None, str | None]:
        key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id).first()
        if not key:
            return None, None

        if data.name is not None:
            key.name = data.name.strip()
        if data.group_name is not None:
            key.group_name = data.group_name.strip() or "default"
        if data.status is not None:
            if data.status not in VALID_KEY_STATUSES:
                return key, f"非法 status 值，可选: {', '.join(VALID_KEY_STATUSES)}"
            key.status = data.status
        if data.allowed_models is not None:
            try:
                key.allowed_models = self._normalize_allowed_models(data.allowed_models, db)
            except ValueError as exc:
                return key, str(exc)
        if data.expires_at is not None:
            key.expires_at = data.expires_at

        db.commit()
        db.refresh(key)
        return key, None

    def get_by_key_value(self, key_value: str, db: Session) -> APIKey | None:
        return db.query(APIKey).filter(APIKey.key_value == key_value).first()

    def get_first_active_key(self, user_id: int, db: Session) -> APIKey | None:
        now = datetime.now(timezone.utc)
        keys = (
            db.query(APIKey)
            .filter(APIKey.user_id == user_id, APIKey.status == KEY_STATUS_ACTIVE)
            .order_by(APIKey.created_at.asc())
            .all()
        )
        for key in keys:
            expires_at = self._normalize_dt(key.expires_at)
            if expires_at is None or expires_at > now:
                return key
        return None

    def delete_key(self, key_id: int, user_id: int, db: Session) -> bool:
        key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id).first()
        if not key:
            return False
        db.delete(key)
        db.commit()
        return True


key_service = KeyService()
