from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.proxy_errors import ProxyBaseException
from app.models.provider import Provider
from app.models.provider_key import ProviderKey
from app.models.proxy_request_log import ProxyRequestLog
from app.schemas.admin_proxy_tester import (
    AdminProxyTesterOptionsResponse,
    AdminProxyTesterRequest,
    AdminProxyTesterResponse,
)
from app.services.model_route_service import model_route_service
from app.services.provider_key_service import provider_key_service
from app.services.provider_service import provider_service
from app.services.proxy_gateway_service import proxy_gateway_service
from app.services.proxy_log_service import proxy_log_service
from app.services.route_policy_service import route_policy_service


class ProxyTesterService:
    REQUEST_ORIGIN = "admin_tester"

    def get_options(self, db: Session) -> AdminProxyTesterOptionsResponse:
        return AdminProxyTesterOptionsResponse(
            models=[item for item in model_route_service.list_enriched(db) if item.get("is_active")],
            providers=provider_service.list_enriched(db),
            provider_keys=provider_key_service.list_enriched(db, status="active"),
            route_policies=route_policy_service.list_enriched(db),
        )

    def _get_route_context(self, public_model_name: str, db: Session) -> tuple[object, set[int], dict[int, tuple[int, datetime | None, str | None]]]:
        route = model_route_service.resolve(public_model_name, db)
        if not route or not route.is_active:
            raise HTTPException(status_code=400, detail="当前公版模型没有可用的模型映射，请先配置并启用 Model Route")

        allowed_provider_ids = {route.provider_id}
        if route.fallback_provider_id:
            allowed_provider_ids.add(route.fallback_provider_id)

        key_snapshots: dict[int, tuple[int, datetime | None, str | None]] = {}
        for key in db.query(ProviderKey).filter(ProviderKey.provider_id.in_(allowed_provider_ids)).all():
            key_snapshots[key.id] = (key.used_count_today, key.last_used_at, key.last_error)
        return route, allowed_provider_ids, key_snapshots

    def _resolve_forced_targets(
        self,
        data: AdminProxyTesterRequest,
        allowed_provider_ids: set[int],
        db: Session,
    ) -> tuple[int | None, int | None]:
        forced_provider_id: int | None = None
        forced_provider_key_id: int | None = None

        if data.route_mode == "provider":
            forced_provider_id = data.provider_id
            if forced_provider_id not in allowed_provider_ids:
                raise HTTPException(status_code=400, detail="指定的 Provider 不在当前模型映射的候选链路中")

        if data.route_mode == "provider_key":
            if not data.provider_key_id:
                raise HTTPException(status_code=400, detail="指定 Source Key 模式下必须选择 Source Key")
            key = provider_key_service.get(data.provider_key_id, db)
            if not key:
                raise HTTPException(status_code=400, detail="指定的 Source Key 不存在")
            if key.provider_id not in allowed_provider_ids:
                raise HTTPException(status_code=400, detail="指定的 Source Key 不属于当前模型映射的候选 Provider")
            forced_provider_id = key.provider_id
            forced_provider_key_id = key.id

        return forced_provider_id, forced_provider_key_id

    async def run_test(self, data: AdminProxyTesterRequest, db: Session) -> AdminProxyTesterResponse:
        route, allowed_provider_ids, key_snapshots = self._get_route_context(data.public_model_name, db)
        forced_provider_id, forced_provider_key_id = self._resolve_forced_targets(data, allowed_provider_ids, db)
        policy = route_policy_service.get_for_model(data.public_model_name, db)

        request_tag = f"admin-test-{uuid4().hex[:24]}"
        started_at = datetime.now(timezone.utc)
        gateway_response: dict | None = None
        success = False
        status_code = 200
        error_summary: str | None = None

        try:
            gateway_response = await proxy_gateway_service.execute_chat_completion(
                public_model=data.public_model_name,
                messages=[item.model_dump() for item in data.messages],
                user_id=None,
                user_api_key_id=None,
                db=db,
                temperature=data.temperature,
                max_tokens=data.max_tokens,
                stream=data.stream,
                include_debug=True,
                forced_provider_id=forced_provider_id,
                forced_provider_key_id=forced_provider_key_id,
                request_origin=self.REQUEST_ORIGIN,
                request_tag=request_tag,
            )
            success = True
        except ProxyBaseException as exc:
            http_exc = exc.to_http()
            status_code = http_exc.status_code
            error_summary = str(http_exc.detail)
        except HTTPException as exc:
            status_code = exc.status_code
            error_summary = str(exc.detail)
        except Exception as exc:
            status_code = 500
            error_summary = str(exc)

        elapsed_ms = round((datetime.now(timezone.utc) - started_at).total_seconds() * 1000, 2)
        log_record = proxy_log_service.get_latest_by_request_tag(db, request_tag)

        provider: Provider | None = None
        provider_key: ProviderKey | None = None
        if log_record and log_record.provider_id:
            provider = db.query(Provider).filter(Provider.id == log_record.provider_id).first()
        if log_record and log_record.provider_key_id:
            provider_key = db.query(ProviderKey).filter(ProviderKey.id == log_record.provider_key_id).first()

        debug = gateway_response.get("debug") if gateway_response else {}
        usage = gateway_response.get("usage") if gateway_response else None
        assistant_message = None
        if gateway_response and gateway_response.get("choices"):
            assistant_message = gateway_response["choices"][0].get("message", {}).get("content")

        source_key_usage_updated = False
        source_key_last_used_at = None
        source_key_used_count_today = None
        if provider_key:
            before = key_snapshots.get(provider_key.id)
            if before:
                before_used_count, before_last_used_at, _ = before
                source_key_usage_updated = (
                    provider_key.used_count_today != before_used_count
                    or provider_key.last_used_at != before_last_used_at
                )
            source_key_last_used_at = provider_key.last_used_at
            source_key_used_count_today = provider_key.used_count_today

        return AdminProxyTesterResponse(
            success=success,
            status_code=status_code,
            route_mode=data.route_mode,
            public_model_name=data.public_model_name,
            assistant_message=assistant_message,
            error_summary=error_summary,
            request_id=(gateway_response or {}).get("id") or (log_record.request_id if log_record else None),
            request_log_id=log_record.id if log_record else debug.get("request_log_id"),
            request_origin=self.REQUEST_ORIGIN,
            request_tag=request_tag,
            request_status=log_record.request_status if log_record else ("success" if success else "error"),
            latency_ms=debug.get("latency_ms") or (log_record.latency_ms if log_record else elapsed_ms),
            provider_id=(log_record.provider_id if log_record else debug.get("provider_id")),
            provider_name=(provider.name if provider else debug.get("provider_name")),
            provider_type=(provider.provider_type if provider else debug.get("provider_type")),
            provider_key_id=(log_record.provider_key_id if log_record else debug.get("provider_key_id")),
            provider_key_name=(provider_key.name if provider_key else debug.get("provider_key_name")),
            policy_name=debug.get("policy_name") or (policy.name if policy else None),
            policy_type=(log_record.policy_type if log_record else debug.get("policy_type") or (policy.policy_type if policy else None)),
            upstream_model_name=(log_record.provider_model_name if log_record else debug.get("upstream_model_name")),
            fallback_triggered=(log_record.fallback_triggered if log_record else bool(debug.get("fallback_triggered"))),
            provider_switch_count=(log_record.provider_switch_count if log_record else int(debug.get("provider_switch_count") or 0)),
            key_switch_count=(log_record.key_switch_count if log_record else int(debug.get("key_switch_count") or 0)),
            failure_chain_summary=(log_record.failure_chain_summary if log_record else debug.get("failure_chain_summary")),
            log_written=log_record is not None,
            source_key_usage_updated=source_key_usage_updated,
            source_key_last_used_at=source_key_last_used_at,
            source_key_used_count_today=source_key_used_count_today,
            forced_provider_honored=(None if forced_provider_id is None else bool(log_record and log_record.provider_id == forced_provider_id)),
            forced_source_key_honored=(None if forced_provider_key_id is None else bool(log_record and log_record.provider_key_id == forced_provider_key_id)),
            usage=usage,
        )


proxy_tester_service = ProxyTesterService()
