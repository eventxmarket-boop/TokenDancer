from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from app.core.constants import VALID_KEY_STATUSES
from app.core.crypto import encrypt_api_key, mask_api_key
from app.models.provider import Provider
from app.models.provider_key import ProviderKey
from app.models.proxy_request_log import ProxyRequestLog
from app.schemas.provider_key import ProviderKeyCreate, ProviderKeyUpdate


class ProviderKeyService:
    def list_keys(self, db: Session, provider_id: int | None = None, status: str | None = None) -> List[ProviderKey]:
        query = db.query(ProviderKey)
        if provider_id:
            query = query.filter(ProviderKey.provider_id == provider_id)
        if status:
            query = query.filter(ProviderKey.status == status)
        return query.order_by(ProviderKey.created_at.desc()).all()

    def list_enriched(self, db: Session, provider_id: int | None = None, status: str | None = None) -> list[dict]:
        return [self.serialize(item, db) for item in self.list_keys(db, provider_id=provider_id, status=status)]

    def get(self, key_id: int, db: Session) -> ProviderKey | None:
        return db.query(ProviderKey).filter(ProviderKey.id == key_id).first()

    def get_enriched(self, key_id: int, db: Session) -> dict | None:
        key = self.get(key_id, db)
        if not key:
            return None
        return self.serialize(key, db)

    def _get_provider(self, provider_id: int, db: Session) -> Provider | None:
        return db.query(Provider).filter(Provider.id == provider_id).first()

    def _normalize_supported_models(self, value: str | None) -> str | None:
        if value is None:
            return None
        models = [item.strip() for item in value.split(",") if item.strip()]
        return ", ".join(dict.fromkeys(models)) or None

    def _normalize_status(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in VALID_KEY_STATUSES:
            raise ValueError(f"非法 Key 状态，可选: {', '.join(sorted(VALID_KEY_STATUSES))}")
        return normalized

    def create(self, data: ProviderKeyCreate, db: Session) -> ProviderKey:
        provider = self._get_provider(data.provider_id, db)
        if not provider:
            raise ValueError("所属 Provider 不存在，请先创建 Provider")

        encrypted = encrypt_api_key(data.api_key)
        masked = mask_api_key(data.api_key)
        kwargs = data.model_dump(exclude={"api_key"})
        kwargs["supported_models"] = self._normalize_supported_models(kwargs.get("supported_models"))
        kwargs["status"] = self._normalize_status(kwargs.get("status")) or "active"
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
        if "provider_id" in update and update["provider_id"] is not None:
            provider = self._get_provider(update["provider_id"], db)
            if not provider:
                raise ValueError("目标 Provider 不存在，请先创建 Provider")
        if "supported_models" in update:
            update["supported_models"] = self._normalize_supported_models(update.get("supported_models"))
        if "status" in update:
            update["status"] = self._normalize_status(update.get("status"))
        if "api_key" in update and update["api_key"]:
            raw_key = update.pop("api_key")
            update["key_encrypted"] = encrypt_api_key(raw_key)
            update["key_masked"] = mask_api_key(raw_key)
        elif "api_key" in update:
            update.pop("api_key")
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

    def get_available_keys_for_model(self, provider_id: int, model_name: str, db: Session) -> List[ProviderKey]:
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

    def serialize(self, key: ProviderKey, db: Session) -> dict:
        provider = self._get_provider(key.provider_id, db)
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        logs = (
            db.query(ProxyRequestLog)
            .filter(
                ProxyRequestLog.provider_key_id == key.id,
                ProxyRequestLog.requested_at >= since,
            )
            .all()
        )
        success_count = len([log for log in logs if log.request_status == "success"])
        failure_count = len(logs) - success_count
        return {
            "id": key.id,
            "provider_id": key.provider_id,
            "provider_name": provider.name if provider else None,
            "provider_type": provider.provider_type if provider else None,
            "provider_health_status": provider.health_status if provider else None,
            "name": key.name,
            "key_masked": key.key_masked,
            "supported_models": key.supported_models,
            "status": key.status,
            "weight": key.weight,
            "rpm_limit": key.rpm_limit,
            "daily_limit": key.daily_limit,
            "used_count_today": key.used_count_today,
            "last_used_at": key.last_used_at,
            "last_error": key.last_error,
            "notes": key.notes,
            "created_at": key.created_at,
            "request_count_24h": len(logs),
            "success_count_24h": success_count,
            "failure_count_24h": failure_count,
        }


provider_key_service = ProviderKeyService()
