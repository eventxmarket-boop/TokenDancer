from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.constants import PROVIDER_DEFAULT_BASE_URLS, VALID_PROVIDER_TYPES
from app.models.provider import Provider
from app.schemas.provider import ProviderCreate, ProviderUpdate


class ProviderService:
    def list(self, db: Session) -> list[Provider]:
        return db.query(Provider).order_by(Provider.priority.asc()).all()

    def get(self, provider_id: int, db: Session) -> Provider | None:
        return db.query(Provider).filter(Provider.id == provider_id).first()

    def _normalize_payload(self, payload: dict) -> dict:
        normalized = dict(payload)
        if "name" in normalized and normalized["name"] is not None:
            normalized["name"] = normalized["name"].strip()
        if "notes" in normalized and normalized["notes"] is not None:
            normalized["notes"] = normalized["notes"].strip() or None
        if "provider_type" in normalized and normalized["provider_type"] is not None:
            provider_type = str(normalized["provider_type"]).strip().lower()
            if provider_type not in VALID_PROVIDER_TYPES:
                raise ValueError(f"非法 provider_type，可选: {', '.join(sorted(VALID_PROVIDER_TYPES))}")
            normalized["provider_type"] = provider_type
            base_url = (normalized.get("base_url") or "").strip().rstrip("/")
            normalized["base_url"] = base_url or PROVIDER_DEFAULT_BASE_URLS.get(provider_type)
        elif "base_url" in normalized and normalized["base_url"] is not None:
            normalized["base_url"] = normalized["base_url"].strip().rstrip("/") or None
        return normalized

    def create(self, data: ProviderCreate, db: Session) -> Provider:
        payload = self._normalize_payload(data.model_dump())
        provider = Provider(**payload)
        db.add(provider)
        db.commit()
        db.refresh(provider)
        return provider

    def update(self, provider_id: int, data: ProviderUpdate, db: Session) -> Provider | None:
        provider = self.get(provider_id, db)
        if not provider:
            return None
        update = self._normalize_payload(data.model_dump(exclude_unset=True))
        for field, value in update.items():
            setattr(provider, field, value)
        db.commit()
        db.refresh(provider)
        return provider

    def update_health(self, provider_id: int, status: str, db: Session) -> Provider | None:
        provider = self.get(provider_id, db)
        if not provider:
            return None
        provider.health_status = status
        provider.last_health_check_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(provider)
        return provider


provider_service = ProviderService()
