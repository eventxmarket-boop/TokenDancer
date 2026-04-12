from datetime import datetime, timedelta, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.model_route import ModelRoute
from app.models.provider import Provider
from app.models.provider_key import ProviderKey
from app.models.proxy_request_log import ProxyRequestLog
from app.services.proxy_gateway_service import proxy_gateway_service
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
        }

    def providers(self, db: Session) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        logs = (
            db.query(ProxyRequestLog)
            .filter(ProxyRequestLog.requested_at >= since)
            .order_by(desc(ProxyRequestLog.requested_at))
            .all()
        )
        provider_logs: dict[int, list[ProxyRequestLog]] = {}
        for log in logs:
            if log.provider_id is None:
                continue
            provider_logs.setdefault(log.provider_id, []).append(log)

        rows = []
        providers = db.query(Provider).order_by(Provider.priority.asc(), Provider.id.asc()).all()
        for provider in providers:
            logs_for_provider = provider_logs.get(provider.id, [])
            success_logs = [log for log in logs_for_provider if log.request_status == "success"]
            failed_logs = [log for log in logs_for_provider if log.request_status != "success"]
            last_log = logs_for_provider[0] if logs_for_provider else None
            keys = db.query(ProviderKey).filter(ProviderKey.provider_id == provider.id).all()
            runtime = proxy_gateway_service.get_provider_runtime_snapshot(provider.id)
            rows.append(
                {
                    "id": provider.id,
                    "name": provider.name,
                    "provider_type": provider.provider_type,
                    "base_url": provider.base_url,
                    "is_active": provider.is_active,
                    "health_status": provider.health_status,
                    "last_health_check_at": provider.last_health_check_at.isoformat() if provider.last_health_check_at else None,
                    "priority": provider.priority,
                    "active_key_count": len([key for key in keys if key.status == "active"]),
                    "request_count_24h": len(logs_for_provider),
                    "success_rate_24h": round(len(success_logs) / len(logs_for_provider) * 100, 2) if logs_for_provider else 0.0,
                    "avg_latency_ms_24h": round(sum(log.latency_ms or 0 for log in success_logs) / len(success_logs), 2) if success_logs else 0.0,
                    "recent_failures_24h": len(failed_logs),
                    "last_error": last_log.error_message if last_log and last_log.request_status != "success" else runtime.get("last_error"),
                    "cooldown_active": runtime["cooldown_active"],
                    "cooldown_remaining_seconds": runtime["cooldown_remaining_seconds"],
                }
            )
        return rows

    def models(self, db: Session) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        routes = db.query(ModelRoute).order_by(ModelRoute.priority.asc(), ModelRoute.id.asc()).all()
        providers = {provider.id: provider for provider in db.query(Provider).all()}
        logs = db.query(ProxyRequestLog).filter(ProxyRequestLog.requested_at >= since).all()
        log_map: dict[str, list[ProxyRequestLog]] = {}
        for log in logs:
            log_map.setdefault(log.public_model_name, []).append(log)

        rows = []
        for route in routes:
            policy = route_policy_service.get_for_model(route.public_model_name, db)
            model_logs = log_map.get(route.public_model_name, [])
            success_logs = [log for log in model_logs if log.request_status == "success"]
            failed_logs = [log for log in model_logs if log.request_status != "success"]
            last_log = model_logs[0] if model_logs else None
            rows.append(
                {
                    "id": route.id,
                    "public_model_name": route.public_model_name,
                    "provider_id": route.provider_id,
                    "provider_name": providers.get(route.provider_id).name if providers.get(route.provider_id) else None,
                    "provider_model_name": route.provider_model_name,
                    "fallback_provider_id": route.fallback_provider_id,
                    "fallback_provider_name": providers.get(route.fallback_provider_id).name if providers.get(route.fallback_provider_id) else None,
                    "fallback_model_name": route.fallback_model_name,
                    "policy_type": policy.policy_type if policy else "fixed",
                    "priority": route.priority,
                    "cost_multiplier": float(route.cost_multiplier or 1.0),
                    "is_active": route.is_active,
                    "request_count_24h": len(model_logs),
                    "success_rate_24h": round(len(success_logs) / len(model_logs) * 100, 2) if model_logs else 0.0,
                    "avg_latency_ms_24h": round(sum(log.latency_ms or 0 for log in success_logs) / len(success_logs), 2) if success_logs else 0.0,
                    "failure_count_24h": len(failed_logs),
                    "last_request_at": last_log.requested_at.isoformat() if last_log and last_log.requested_at else None,
                    "last_error": failed_logs[0].error_message if failed_logs else None,
                }
            )
        return rows

    def failures(self, db: Session, limit: int = 20) -> list[dict]:
        providers = {provider.id: provider.name for provider in db.query(Provider).all()}
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
                "provider_name": providers.get(record.provider_id),
                "request_status": record.request_status,
                "latency_ms": record.latency_ms,
                "error_message": record.error_message,
                "failure_chain_summary": record.failure_chain_summary,
                "fallback_triggered": record.fallback_triggered,
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
        db.commit()
        db.refresh(route)

        return {
            "id": route.id,
            "public_model_name": route.public_model_name,
            "provider_id": route.provider_id,
            "fallback_provider_id": route.fallback_provider_id,
            "provider_model_name": route.provider_model_name,
            "fallback_model_name": route.fallback_model_name,
            "message": "主备路由已切换",
        }


proxy_monitor_service = ProxyMonitorService()
