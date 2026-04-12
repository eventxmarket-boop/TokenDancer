from datetime import datetime, timedelta, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.model_route import ModelRoute
from app.models.provider import Provider
from app.models.provider_key import ProviderKey
from app.models.proxy_request_log import ProxyRequestLog
from app.services.model_route_service import model_route_service
from app.services.provider_key_service import provider_key_service
from app.services.provider_service import provider_service
from app.services.route_policy_service import route_policy_service


class ProxyMonitorService:
    def overview(self, db: Session) -> dict:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        logs = (
            db.query(ProxyRequestLog)
            .filter(ProxyRequestLog.requested_at >= since)
            .order_by(desc(ProxyRequestLog.requested_at))
            .all()
        )
        providers = db.query(Provider).all()
        active_routes = db.query(ModelRoute).filter(ModelRoute.is_active == True).all()

        total_requests = len(logs)
        success_logs = [log for log in logs if log.request_status == "success"]
        failed_logs = [log for log in logs if log.request_status != "success"]
        avg_latency = round(sum(log.latency_ms or 0 for log in success_logs) / len(success_logs), 2) if success_logs else 0.0
        success_rate = round(len(success_logs) / total_requests * 100, 2) if total_requests else 0.0

        return {
            "total_requests_24h": total_requests,
            "success_rate_24h": success_rate,
            "failed_requests_24h": len(failed_logs),
            "avg_latency_ms_24h": avg_latency,
            "healthy_provider_count": len([provider for provider in providers if provider.health_status == "healthy"]),
            "active_provider_count": len([provider for provider in providers if provider.is_active]),
            "active_model_count": len(active_routes),
            "active_provider_key_count": db.query(ProviderKey).filter(ProviderKey.status == "active").count(),
        }

    def providers(self, db: Session) -> list[dict]:
        return provider_service.list_enriched(db)

    def models(self, db: Session) -> list[dict]:
        return model_route_service.list_enriched(db)

    def failures(self, db: Session, limit: int = 20) -> list[dict]:
        providers = {provider.id: provider for provider in db.query(Provider).all()}
        provider_keys = {item.id: item for item in db.query(ProviderKey).all()}
        records = (
            db.query(ProxyRequestLog)
            .filter(ProxyRequestLog.request_status != "success")
            .order_by(desc(ProxyRequestLog.requested_at))
            .limit(limit)
            .all()
        )
        return [
            {
                "id": record.id,
                "requested_at": record.requested_at.isoformat() if record.requested_at else None,
                "public_model_name": record.public_model_name,
                "provider_id": record.provider_id,
                "provider_name": providers.get(record.provider_id).name if providers.get(record.provider_id) else None,
                "provider_type": providers.get(record.provider_id).provider_type if providers.get(record.provider_id) else None,
                "provider_key_id": record.provider_key_id,
                "provider_key_name": provider_keys.get(record.provider_key_id).name if provider_keys.get(record.provider_key_id) else None,
                "request_status": record.request_status,
                "latency_ms": record.latency_ms,
                "error_message": record.error_message,
                "failure_chain_summary": record.failure_chain_summary,
                "fallback_triggered": record.fallback_triggered,
                "policy_type": record.policy_type,
            }
            for record in records
        ]

    def switch_route(self, route_id: int, db: Session, mode: str = "swap") -> dict:
        route = db.query(ModelRoute).filter(ModelRoute.id == route_id).first()
        if not route:
            raise ValueError("模型路由不存在")
        if not route.fallback_provider_id:
            raise ValueError("当前模型未配置备用路由，无法切换")
        if mode != "swap":
            raise ValueError("当前仅支持 swap 切换模式")

        route.provider_id, route.fallback_provider_id = route.fallback_provider_id, route.provider_id
        route.provider_model_name, route.fallback_model_name = (
            route.fallback_model_name or route.provider_model_name,
            route.provider_model_name,
        )

        policy = route_policy_service.get_for_model(route.public_model_name, db)
        if policy:
            if policy.primary_provider_id == route.fallback_provider_id:
                policy.primary_provider_id = route.provider_id
            elif policy.primary_provider_id == route.provider_id and route.fallback_provider_id:
                policy.primary_provider_id = route.provider_id
            if policy.secondary_provider_id is not None:
                if policy.secondary_provider_id == route.provider_id:
                    policy.secondary_provider_id = route.fallback_provider_id
                elif route.fallback_provider_id and policy.secondary_provider_id == route.fallback_provider_id:
                    policy.secondary_provider_id = route.provider_id

        db.commit()
        db.refresh(route)
        return model_route_service.serialize(route, db)


proxy_monitor_service = ProxyMonitorService()
