from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from app.core.constants import PROVIDER_DEFAULT_BASE_URLS, VALID_PROVIDER_TYPES
from app.models.provider import Provider
from app.models.provider_key import ProviderKey
from app.models.proxy_request_log import ProxyRequestLog
from app.schemas.provider import ProviderCreate, ProviderUpdate


class ProviderService:
    def list_providers(self, db: Session) -> List[Provider]:
        return db.query(Provider).order_by(Provider.priority.asc(), Provider.id.asc()).all()

    def list_enriched(self, db: Session) -> list[dict]:
        return [self.serialize(provider, db) for provider in self.list_providers(db)]

    def get(self, provider_id: int, db: Session) -> Provider | None:
        return db.query(Provider).filter(Provider.id == provider_id).first()

    def get_enriched(self, provider_id: int, db: Session) -> dict | None:
        provider = self.get(provider_id, db)
        if not provider:
            return None
        return self.serialize(provider, db)

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

    def serialize(self, provider: Provider, db: Session) -> dict:
        from app.services.proxy_gateway_service import proxy_gateway_service

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        logs = (
            db.query(ProxyRequestLog)
            .filter(
                ProxyRequestLog.provider_id == provider.id,
                ProxyRequestLog.requested_at >= since,
            )
            .all()
        )
        success_logs = [log for log in logs if log.request_status == "success"]
        failed_logs = [log for log in logs if log.request_status != "success"]
        runtime = proxy_gateway_service.get_provider_runtime_snapshot(provider.id)
        active_key_count = (
            db.query(ProviderKey)
            .filter(ProviderKey.provider_id == provider.id, ProviderKey.status == "active")
            .count()
        )
        last_failed_log = next((log for log in logs if log.request_status != "success"), None)
        return {
            "id": provider.id,
            "name": provider.name,
            "provider_type": provider.provider_type,
            "base_url": provider.base_url,
            "is_active": provider.is_active,
            "priority": provider.priority,
            "timeout_seconds": provider.timeout_seconds,
            "notes": provider.notes,
            "health_status": provider.health_status,
            "last_health_check_at": provider.last_health_check_at,
            "created_at": provider.created_at,
            "active_key_count": active_key_count,
            "request_count_24h": len(logs),
            "success_rate_24h": round(len(success_logs) / len(logs) * 100, 2) if logs else 0.0,
            "avg_latency_ms_24h": round(sum(log.latency_ms or 0 for log in success_logs) / len(success_logs), 2) if success_logs else 0.0,
            "recent_failures_24h": len(failed_logs),
            "last_error": last_failed_log.error_message if last_failed_log else runtime.get("last_error"),
            "cooldown_active": runtime["cooldown_active"],
            "cooldown_remaining_seconds": runtime["cooldown_remaining_seconds"],
        }


provider_service = ProviderService()
