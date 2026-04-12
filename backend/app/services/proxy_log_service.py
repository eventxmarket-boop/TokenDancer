from datetime import datetime, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.provider import Provider
from app.models.provider_key import ProviderKey
from app.models.proxy_request_log import ProxyRequestLog


class ProxyLogService:
    def create(
        self,
        db: Session,
        user_id: int | None,
        user_api_key_id: int | None,
        public_model_name: str,
        provider_id: int | None,
        provider_key_id: int | None,
        provider_model_name: str,
        request_status: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int | None,
        cost: float,
        latency_ms: int,
        error_message: str | None,
        request_id: str | None,
        upstream_provider_id: int | None = None,
        upstream_key_id: int | None = None,
        policy_type: str = "fixed",
        fallback_triggered: bool = False,
        retry_attempt: int = 0,
    ) -> ProxyRequestLog:
        if total_tokens is None:
            total_tokens = input_tokens + output_tokens
        log = ProxyRequestLog(
            request_id=request_id,
            user_id=user_id,
            user_api_key_id=user_api_key_id,
            public_model_name=public_model_name,
            provider_id=provider_id,
            provider_key_id=provider_key_id,
            provider_model_name=provider_model_name,
            request_status=request_status,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=cost,
            latency_ms=latency_ms,
            error_message=error_message,
            requested_at=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def write(
        self,
        user_id: int | None,
        user_api_key_id: int | None,
        public_model: str,
        provider_id: int | None,
        provider_key_id: int | None,
        provider_model_name: str,
        status: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        latency_ms: int,
        error_message: str | None,
        request_id: str | None,
        db: Session,
        upstream_provider_id: int | None = None,
        upstream_key_id: int | None = None,
        request_origin: str = "proxy",
        request_tag: str | None = None,
        policy_type: str = "fixed",
        fallback_triggered: bool = False,
        retry_attempt: int = 0,
        provider_switch_count: int = 0,
        key_switch_count: int = 0,
        failure_chain_summary: str | None = None,
    ) -> ProxyRequestLog:
        log = ProxyRequestLog(
            request_id=request_id,
            user_id=user_id,
            user_api_key_id=user_api_key_id,
            public_model_name=public_model,
            provider_id=provider_id,
            provider_key_id=provider_key_id,
            provider_model_name=provider_model_name,
            request_status=status,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=cost,
            latency_ms=latency_ms,
            error_message=error_message,
            requested_at=datetime.now(timezone.utc),
            upstream_provider_id=upstream_provider_id,
            upstream_key_id=upstream_key_id,
            request_origin=request_origin,
            request_tag=request_tag,
            policy_type=policy_type,
            fallback_triggered=fallback_triggered,
            retry_attempt=retry_attempt,
            provider_switch_count=provider_switch_count,
            key_switch_count=key_switch_count,
            failure_chain_summary=failure_chain_summary,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def get_latest_by_request_tag(self, db: Session, request_tag: str) -> ProxyRequestLog | None:
        return (
            db.query(ProxyRequestLog)
            .filter(ProxyRequestLog.request_tag == request_tag)
            .order_by(desc(ProxyRequestLog.requested_at), desc(ProxyRequestLog.id))
            .first()
        )

    def query(
        self,
        db: Session,
        provider_id: int | None = None,
        public_model_name: str | None = None,
        request_status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        q = db.query(ProxyRequestLog)
        if provider_id:
            q = q.filter(ProxyRequestLog.provider_id == provider_id)
        if public_model_name:
            q = q.filter(ProxyRequestLog.public_model_name == public_model_name)
        if request_status:
            q = q.filter(ProxyRequestLog.request_status == request_status)
        if date_from:
            q = q.filter(ProxyRequestLog.requested_at >= date_from)
        if date_to:
            q = q.filter(ProxyRequestLog.requested_at <= date_to)
        records = (
            q.order_by(desc(ProxyRequestLog.requested_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
        provider_ids = {record.provider_id for record in records if record.provider_id is not None}
        provider_key_ids = {record.provider_key_id for record in records if record.provider_key_id is not None}
        providers = {
            item.id: item
            for item in db.query(Provider).filter(Provider.id.in_(provider_ids)).all()
        } if provider_ids else {}
        provider_keys = {
            item.id: item
            for item in db.query(ProviderKey).filter(ProviderKey.id.in_(provider_key_ids)).all()
        } if provider_key_ids else {}
        return [
            {
                "id": record.id,
                "request_id": record.request_id,
                "user_id": record.user_id,
                "user_api_key_id": record.user_api_key_id,
                "public_model_name": record.public_model_name,
                "provider_id": record.provider_id,
                "provider_name": providers.get(record.provider_id).name if providers.get(record.provider_id) else None,
                "provider_type": providers.get(record.provider_id).provider_type if providers.get(record.provider_id) else None,
                "provider_key_id": record.provider_key_id,
                "provider_key_name": provider_keys.get(record.provider_key_id).name if provider_keys.get(record.provider_key_id) else None,
                "request_origin": record.request_origin,
                "request_tag": record.request_tag,
                "provider_model_name": record.provider_model_name,
                "request_status": record.request_status,
                "input_tokens": record.input_tokens,
                "output_tokens": record.output_tokens,
                "total_tokens": record.total_tokens,
                "cost": float(record.cost or 0),
                "latency_ms": record.latency_ms,
                "error_message": record.error_message,
                "requested_at": record.requested_at,
                "upstream_provider_id": record.upstream_provider_id,
                "upstream_key_id": record.upstream_key_id,
                "policy_type": record.policy_type,
                "fallback_triggered": record.fallback_triggered,
                "retry_attempt": record.retry_attempt,
                "provider_switch_count": record.provider_switch_count,
                "key_switch_count": record.key_switch_count,
                "failure_chain_summary": record.failure_chain_summary,
            }
            for record in records
        ]


proxy_log_service = ProxyLogService()
