from sqlalchemy.orm import Session

from app.core.crypto import encrypt_api_key, mask_api_key
from app.models.provider import Provider
from app.models.provider_key import ProviderKey
from app.schemas.provider_key import ProviderKeyCreate, ProviderKeyUpdate


class ProviderKeyService:
    def list(self, db: Session, provider_id: int | None = None) -> list[ProviderKey]:
        query = db.query(ProviderKey)
        if provider_id:
            query = query.filter(ProviderKey.provider_id == provider_id)
        return query.order_by(ProviderKey.created_at.desc()).all()

    def get(self, key_id: int, db: Session) -> ProviderKey | None:
        return db.query(ProviderKey).filter(ProviderKey.id == key_id).first()

    def _get_provider(self, provider_id: int, db: Session) -> Provider | None:
        return db.query(Provider).filter(Provider.id == provider_id).first()

    def _normalize_supported_models(self, value: str | None) -> str | None:
        if value is None:
            return None
        models = [item.strip() for item in value.split(",") if item.strip()]
        return ", ".join(dict.fromkeys(models)) or None

    def create(self, data: ProviderKeyCreate, db: Session) -> ProviderKey:
        provider = self._get_provider(data.provider_id, db)
        if not provider:
            raise ValueError("所属 Provider 不存在，请先创建 Provider")

        encrypted = encrypt_api_key(data.api_key)
        masked = mask_api_key(data.api_key)
        kwargs = data.model_dump(exclude={"api_key"})
        kwargs["supported_models"] = self._normalize_supported_models(kwargs.get("supported_models"))
        kwargs["key_encrypted"] = encrypted
        kwargs["key_masked"] = masked
        key = ProviderKey(**kwargs)
        db.add(key)
        db.commit()
        db.refresh(key)
        return key

    def update(self, key_id: int, data: ProviderKeyUpdate, db: Session) -> ProviderKey | None:
        key = self.get(key_id, db)
        if not key:
            return None
        update = data.model_dump(exclude_unset=True)
        if "supported_models" in update:
            update["supported_models"] = self._normalize_supported_models(update.get("supported_models"))
        if "api_key" in update and update["api_key"]:
            raw_key = update.pop("api_key")
            update["key_encrypted"] = encrypt_api_key(raw_key)
            update["key_masked"] = mask_api_key(raw_key)
        for field, value in update.items():
            setattr(key, field, value)
        db.commit()
        db.refresh(key)
        return key

    def get_decrypted(self, key_id: int, db: Session) -> str | None:
        key = self.get(key_id, db)
        if not key:
            return None
        from app.core.crypto import decrypt_api_key
        return decrypt_api_key(key.key_encrypted)

    def is_key_available(self, key: ProviderKey, model_name: str, db: Session) -> tuple[bool, str]:
        if key.status != "active":
            return False, f"status={key.status}"

        if key.supported_models:
            models = [m.strip() for m in key.supported_models.split(",")]
            if model_name not in models:
                return False, f"model '{model_name}' not in supported_models"

        if key.daily_limit > 0 and key.used_count_today >= key.daily_limit:
            return False, f"daily_limit exceeded ({key.used_count_today}/{key.daily_limit})"

        return True, ""

    def get_available_keys_for_model(self, provider_id: int, model_name: str, db: Session) -> list[ProviderKey]:
        keys = (
            db.query(ProviderKey)
            .filter(ProviderKey.provider_id == provider_id)
            .order_by(ProviderKey.id.asc())
            .all()
        )
        available = []
        for key in keys:
            ok, _ = self.is_key_available(key, model_name, db)
            if ok:
                available.append(key)
        return available

    def delete(self, key_id: int, db: Session) -> bool:
        key = self.get(key_id, db)
        if not key:
            return False
        db.delete(key)
        db.commit()
        return True


provider_key_service = ProviderKeyService()
