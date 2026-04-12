from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
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
    ) -> list[ProxyRequestLog]:
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
        return (
            q.order_by(desc(ProxyRequestLog.requested_at))
            .offset(offset)
            .limit(limit)
            .all()
        )


proxy_log_service = ProxyLogService()
