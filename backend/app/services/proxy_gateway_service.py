"""
Proxy Gateway Service — API 中转执行层核心服务。

设计目标：
- 所有 OpenAI 兼容入口统一走这里
- 统一固定/回退/加权/成本优先路由
- 成功请求统一写 UsageRecord / ProxyRequestLog / 账务扣减
- 失败请求不扣费，但保留完整失败链和运行态信息
"""

import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.proxy_errors import (
    AllProvidersFailedError,
    InsufficientBalanceError,
    KeyDecryptionError,
    ModelRouteNotFoundError,
    NoAvailableProviderError,
    ProviderUnavailableError,
    UpstreamAuthError,
    UpstreamServerError,
    UpstreamTimeoutError,
)
from app.models.api_key import APIKey
from app.models.model_route import ModelRoute
from app.models.provider import Provider
from app.models.provider_key import ProviderKey
from app.models.route_policy import RoutePolicy
from app.models.token_grant import TokenGrant
from app.models.user import User
from app.services.key_service import key_service
from app.services.model_route_service import model_route_service
from app.services.provider_key_service import provider_key_service
from app.services.providers import MinimaxAdapter
from app.services.proxy_log_service import proxy_log_service
from app.services.route_policy_service import route_policy_service
from app.services.usage_service import usage_service

logger = logging.getLogger(__name__)


@dataclass
class ProviderCandidate:
    provider: Provider
    upstream_model_name: str
    is_primary: bool
    is_fallback: bool
    weight: int = 100
    estimated_cost: float = 0.0


@dataclass
class CooldownRecord:
    fail_time: float
    cooldown_seconds: int
    last_error: str


_provider_cooldown: dict[int, CooldownRecord] = {}

_ADAPTERS = {
    "minimax": MinimaxAdapter(),
}


class ProxyGatewayService:
    @staticmethod
    def _normalize_dt(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def resolve_route(self, public_model: str, db: Session) -> Optional[ModelRoute]:
        return model_route_service.resolve(public_model, db)

    def list_available_models(self, db: Session, allowed_models: set[str] | None = None) -> list[dict]:
        routes = [route for route in model_route_service.list(db) if route.is_active]
        seen: set[str] = set()
        models: list[dict] = []
        for route in routes:
            public_model = route.public_model_name
            if public_model in seen:
                continue
            if allowed_models is not None and public_model not in allowed_models:
                continue
            seen.add(public_model)
            models.append(
                {
                    "id": public_model,
                    "object": "model",
                    "owned_by": "platform",
                    "public_model_name": public_model,
                }
            )
        models.sort(key=lambda item: item["id"])
        return models

    def get_provider_runtime_snapshot(self, provider_id: int) -> dict:
        record = _provider_cooldown.get(provider_id)
        now = time.time()
        if record and now - record.fail_time >= record.cooldown_seconds:
            del _provider_cooldown[provider_id]
            record = None

        cooldown_remaining = 0
        cooldown_active = False
        last_error = None
        if record:
            cooldown_remaining = max(0, int(record.cooldown_seconds - (now - record.fail_time)))
            cooldown_active = cooldown_remaining > 0
            last_error = record.last_error

        return {
            "provider_id": provider_id,
            "cooldown_active": cooldown_active,
            "cooldown_remaining_seconds": cooldown_remaining,
            "last_error": last_error,
        }

    async def probe_provider(self, provider_id: int, db: Session) -> dict:
        import httpx

        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if not provider:
            raise ValueError("Provider 不存在")

        runtime = self.get_provider_runtime_snapshot(provider.id)
        if not provider.base_url:
            provider.health_status = "unknown"
            provider.last_health_check_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "provider_id": provider.id,
                "provider_name": provider.name,
                "status": provider.health_status,
                "latency_ms": None,
                "http_status": None,
                "cooldown_active": runtime["cooldown_active"],
                "cooldown_remaining_seconds": runtime["cooldown_remaining_seconds"],
                "message": "Provider 未配置 base_url",
            }

        headers = {"Content-Type": "application/json"}
        available_keys = provider_key_service.list(db, provider_id=provider.id)
        raw_key = None
        for key in available_keys:
            if key.status != "active":
                continue
            raw_key = provider_key_service.get_decrypted(key.id, db)
            if raw_key:
                break
        if raw_key:
            headers["Authorization"] = f"Bearer {raw_key}"

        start_time = time.time()
        status = "degraded"
        http_status = None
        message = "探测完成"
        try:
            async with httpx.AsyncClient(timeout=float(provider.timeout_seconds or 10)) as client:
                resp = await client.get(
                    provider.base_url.rstrip("/") + "/models",
                    headers=headers,
                    follow_redirects=True,
                )
                http_status = resp.status_code
                if resp.status_code < 500:
                    status = "healthy"
                else:
                    status = "degraded"
                    message = f"上游返回 {resp.status_code}"
        except httpx.TimeoutException:
            status = "unreachable"
            message = "探测超时"
        except Exception as exc:
            status = "degraded"
            message = f"探测失败: {type(exc).__name__}"

        latency_ms = int((time.time() - start_time) * 1000)
        provider.health_status = status
        provider.last_health_check_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "provider_id": provider.id,
            "provider_name": provider.name,
            "status": status,
            "latency_ms": latency_ms,
            "http_status": http_status,
            "cooldown_active": runtime["cooldown_active"],
            "cooldown_remaining_seconds": runtime["cooldown_remaining_seconds"],
            "message": message,
        }

    async def execute_chat_completion(
        self,
        public_model: str,
        messages: list,
        user_id: int | None,
        user_api_key_id: int | None,
        db: Session,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        include_debug: bool = False,
    ) -> dict:
        route = self.resolve_route(public_model, db)
        if not route:
            raise ModelRouteNotFoundError(public_model)

        policy = route_policy_service.get_for_model(public_model, db)
        policy_type = policy.policy_type if policy else "fixed"
        cooldown_seconds = policy.cooldown_seconds if policy else 60

        candidates = self._build_provider_candidates(route, policy, db)
        if not candidates:
            raise NoAvailableProviderError(
                public_model,
                reason="all candidate providers filtered by active/health/cooldown",
            )

        provider_switch_count = 0
        key_attempt_count = 0
        failure_chain: list[dict] = []
        fallback_triggered = False

        for candidate_index, candidate in enumerate(candidates):
            if candidate.is_fallback:
                fallback_triggered = True
            if candidate_index > 0:
                provider_switch_count += 1

            available_keys = provider_key_service.get_available_keys_for_model(
                candidate.provider.id,
                candidate.upstream_model_name,
                db,
            )
            if not available_keys:
                failure_chain.append(
                    {
                        "provider_id": candidate.provider.id,
                        "key_id": None,
                        "error": "no available provider key",
                    }
                )
                continue

            for key_rec in available_keys:
                key_attempt_count += 1
                raw_key = provider_key_service.get_decrypted(key_rec.id, db)
                if not raw_key:
                    self._update_provider_key_stats(key_rec, db, error="key decryption failed")
                    failure_chain.append(
                        {
                            "provider_id": candidate.provider.id,
                            "key_id": key_rec.id,
                            "error": "key decryption failed",
                        }
                    )
                    continue

                started_at = time.time()
                try:
                    upstream_resp = await self._call_adapter(
                        provider=candidate.provider,
                        api_key=raw_key,
                        model_name=candidate.upstream_model_name,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=stream,
                    )
                    latency_ms = int((time.time() - started_at) * 1000)

                    usage = upstream_resp.usage
                    input_tokens = usage.prompt_tokens
                    output_tokens = usage.completion_tokens
                    total_tokens = usage.total_tokens or (input_tokens + output_tokens)
                    cost_amount = self._calc_cost(
                        input_tokens,
                        output_tokens,
                        self._get_cost_per_million(route, candidate.provider),
                    )

                    billing_info = self._prepare_billing(
                        user_id=user_id,
                        total_tokens=total_tokens,
                        cost_amount=cost_amount,
                        db=db,
                    )
                    if not billing_info["can_afford"]:
                        raise InsufficientBalanceError()

                    effective_api_key_id = self._resolve_effective_usage_api_key_id(
                        user_id=user_id,
                        user_api_key_id=user_api_key_id,
                        db=db,
                    )

                    if user_id is not None and effective_api_key_id is not None:
                        self._charge_user(
                            user_id=user_id,
                            api_key_id=effective_api_key_id,
                            public_model_name=public_model,
                            upstream_model_name=candidate.upstream_model_name,
                            provider_id=candidate.provider.id,
                            provider_key_id=key_rec.id,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            total_tokens=total_tokens,
                            cost_amount=cost_amount,
                            latency_ms=latency_ms,
                            db=db,
                            billing_info=billing_info,
                        )

                    self._write_proxy_log(
                        db=db,
                        user_id=user_id,
                        user_api_key_id=user_api_key_id,
                        public_model=public_model,
                        provider_id=candidate.provider.id,
                        provider_name=candidate.provider.name,
                        provider_key_id=key_rec.id,
                        upstream_model=candidate.upstream_model_name,
                        status="success",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost=cost_amount,
                        latency_ms=latency_ms,
                        error_message=None,
                        request_id=upstream_resp.id,
                        policy_type=policy_type,
                        fallback_triggered=fallback_triggered,
                        provider_switch_count=provider_switch_count,
                        key_switch_count=max(0, key_attempt_count - 1),
                        failure_chain_summary=self._summarize_failures(failure_chain),
                    )

                    self._update_provider_key_stats(key_rec, db, error=None)
                    self._touch_platform_api_key(user_api_key_id, public_model, db)

                    debug_data = None
                    if include_debug:
                        debug_data = {
                            "public_model": public_model,
                            "provider_name": candidate.provider.name,
                            "provider_type": candidate.provider.provider_type,
                            "provider_id": candidate.provider.id,
                            "provider_key_id": key_rec.id,
                            "policy_type": policy_type,
                            "fallback_used": fallback_triggered,
                            "fallback_triggered": fallback_triggered,
                            "provider_switch_count": provider_switch_count,
                            "key_switch_count": max(0, key_attempt_count - 1),
                            "latency_ms": float(latency_ms),
                            "cost": cost_amount,
                            "total_tokens": total_tokens,
                            "upstream_model_name": candidate.upstream_model_name,
                            "failure_chain_summary": self._summarize_failures(failure_chain),
                        }

                    return self._to_openai_response(
                        upstream_resp,
                        public_model,
                        debug_data=debug_data,
                    )

                except InsufficientBalanceError:
                    raise
                except (UpstreamTimeoutError, UpstreamAuthError, UpstreamServerError, KeyDecryptionError) as exc:
                    error_message = self._sanitize_error_message(exc.internal_detail)
                    self._update_provider_key_stats(key_rec, db, error=error_message)
                    failure_chain.append(
                        {
                            "provider_id": candidate.provider.id,
                            "key_id": key_rec.id,
                            "error": error_message,
                        }
                    )
                except Exception as exc:
                    error_message = self._sanitize_error_message(str(exc))
                    self._update_provider_key_stats(key_rec, db, error=error_message)
                    failure_chain.append(
                        {
                            "provider_id": candidate.provider.id,
                            "key_id": key_rec.id,
                            "error": error_message,
                        }
                    )

            last_failure = failure_chain[-1]["error"] if failure_chain else "provider exhausted"
            self._mark_cooldown(candidate.provider, cooldown_seconds, last_failure)
            if policy_type == "fixed":
                self._write_proxy_log(
                    db=db,
                    user_id=user_id,
                    user_api_key_id=user_api_key_id,
                    public_model=public_model,
                    provider_id=candidate.provider.id,
                    provider_name=candidate.provider.name,
                    provider_key_id=None,
                    upstream_model=candidate.upstream_model_name,
                    status="error",
                    input_tokens=0,
                    output_tokens=0,
                    cost=0.0,
                    latency_ms=0,
                    error_message=f"fixed policy provider unavailable: {last_failure}",
                    request_id=None,
                    policy_type=policy_type,
                    fallback_triggered=False,
                    provider_switch_count=provider_switch_count,
                    key_switch_count=max(0, key_attempt_count - 1),
                    failure_chain_summary=self._summarize_failures(failure_chain),
                )
                raise ProviderUnavailableError(candidate.provider.name, reason=last_failure)

        last_error = failure_chain[-1]["error"] if failure_chain else "all providers exhausted"
        final_candidate = candidates[-1] if candidates else None
        self._write_proxy_log(
            db=db,
            user_id=user_id,
            user_api_key_id=user_api_key_id,
            public_model=public_model,
            provider_id=final_candidate.provider.id if final_candidate else None,
            provider_name=final_candidate.provider.name if final_candidate else None,
            provider_key_id=None,
            upstream_model=final_candidate.upstream_model_name if final_candidate else public_model,
            status="error",
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            latency_ms=0,
            error_message=last_error,
            request_id=None,
            policy_type=policy_type,
            fallback_triggered=fallback_triggered,
            provider_switch_count=provider_switch_count,
            key_switch_count=max(0, key_attempt_count - 1),
            failure_chain_summary=self._summarize_failures(failure_chain),
        )
        raise AllProvidersFailedError(public_model, last_error=last_error, failures=failure_chain)

    def _build_provider_candidates(
        self,
        route: ModelRoute,
        policy: Optional[RoutePolicy],
        db: Session,
    ) -> list[ProviderCandidate]:
        policy_type = policy.policy_type if policy else "fixed"
        self._clear_expired_cooldowns()

        candidates: list[ProviderCandidate] = []
        primary = db.query(Provider).filter(Provider.id == route.provider_id).first()
        fallback = None
        if route.fallback_provider_id:
            fallback = db.query(Provider).filter(Provider.id == route.fallback_provider_id).first()

        if self._check_provider_usable(primary):
            candidates.append(
                ProviderCandidate(
                    provider=primary,
                    upstream_model_name=route.provider_model_name,
                    is_primary=True,
                    is_fallback=False,
                    weight=max(1, 100 - int(primary.priority or 0)),
                    estimated_cost=self._estimate_candidate_cost(route, primary),
                )
            )

        if self._check_provider_usable(fallback):
            fallback_weight = max(1, 100 - int((fallback.priority or 0) + 10))
            candidates.append(
                ProviderCandidate(
                    provider=fallback,
                    upstream_model_name=route.fallback_model_name or route.provider_model_name,
                    is_primary=False,
                    is_fallback=True,
                    weight=fallback_weight,
                    estimated_cost=self._estimate_candidate_cost(route, fallback),
                )
            )

        if policy_type == "fixed":
            return [candidate for candidate in candidates if candidate.is_primary]

        if policy_type == "fallback":
            return sorted(candidates, key=lambda item: (not item.is_primary, item.provider.priority or 100))

        if policy_type == "weighted":
            return self._weighted_order(candidates)

        if policy_type == "cost_first":
            return sorted(candidates, key=lambda item: (item.estimated_cost, item.provider.priority or 100))

        return candidates

    def _check_provider_usable(self, provider: Provider | None) -> bool:
        if not provider:
            return False
        if not provider.is_active:
            return False
        if provider.health_status in {"unreachable", "down"}:
            return False
        runtime = self.get_provider_runtime_snapshot(provider.id)
        return not runtime["cooldown_active"]

    def _weighted_order(self, candidates: list[ProviderCandidate]) -> list[ProviderCandidate]:
        if len(candidates) <= 1:
            return candidates

        weighted: list[tuple[float, ProviderCandidate]] = []
        for candidate in candidates:
            weight = max(1, candidate.weight)
            score = random.random() ** (1 / weight)
            weighted.append((score, candidate))
        weighted.sort(key=lambda item: item[0], reverse=True)
        return [candidate for _, candidate in weighted]

    def _clear_expired_cooldowns(self) -> None:
        now = time.time()
        for provider_id in list(_provider_cooldown.keys()):
            record = _provider_cooldown[provider_id]
            if now - record.fail_time >= record.cooldown_seconds:
                del _provider_cooldown[provider_id]

    def _mark_cooldown(self, provider: Provider, cooldown_seconds: int | None, last_error: str) -> None:
        seconds = cooldown_seconds if cooldown_seconds is not None else 60
        if seconds <= 0:
            return
        _provider_cooldown[provider.id] = CooldownRecord(
            fail_time=time.time(),
            cooldown_seconds=seconds,
            last_error=last_error,
        )

    async def _call_adapter(
        self,
        provider: Provider,
        api_key: str,
        model_name: str,
        messages: list,
        temperature: float,
        max_tokens: int | None,
        stream: bool,
    ) -> "UpstreamResponse":
        adapter = _ADAPTERS.get(provider.provider_type)
        if adapter is not None:
            request = adapter.build_upstream_request(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )
            timeout = float(provider.timeout_seconds or 60)
            base_url = provider.base_url if provider.base_url else None
            return await adapter.call(api_key, request, base_url=base_url, timeout=timeout)

        return await self._call_openai_compatible(
            provider,
            api_key,
            model_name,
            messages,
            temperature,
            max_tokens,
            stream,
        )

    async def _call_openai_compatible(
        self,
        provider: Provider,
        api_key: str,
        model_name: str,
        messages: list,
        temperature: float,
        max_tokens: int | None,
        stream: bool,
    ) -> "UpstreamResponse":
        import httpx

        if not provider.base_url:
            raise ValueError(f"Provider {provider.name} has no base_url")

        url = provider.base_url.rstrip("/") + "/chat/completions"
        timeout = float(provider.timeout_seconds or 60)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers, follow_redirects=True)
            except httpx.TimeoutException:
                raise UpstreamTimeoutError(provider.name, timeout)
            except Exception as exc:
                raise UpstreamServerError(provider.name, 502) from exc

        if resp.status_code == 401:
            raise UpstreamAuthError(provider.name)
        if resp.status_code >= 500:
            raise UpstreamServerError(provider.name, resp.status_code)
        if resp.status_code >= 400:
            raise UpstreamServerError(provider.name, resp.status_code)

        data: dict = resp.json()

        from app.services.providers.base import NormalizedUsage, UpstreamResponse

        raw_usage: dict = data.get("usage", {})
        prompt = int(raw_usage.get("prompt_tokens", 0) or 0)
        completion = int(raw_usage.get("completion_tokens", 0) or 0)
        total = int(raw_usage.get("total_tokens", 0) or 0) or prompt + completion

        return UpstreamResponse(
            id=data.get("id", "chatcmpl"),
            model=data.get("model", model_name),
            choices=data.get("choices", []),
            usage=NormalizedUsage(prompt, completion, total),
            raw=data,
        )

    def _estimate_candidate_cost(self, route: ModelRoute, provider: Provider) -> float:
        return self._get_cost_per_million(route, provider)

    def _get_cost_per_million(self, route: ModelRoute, provider: Provider) -> float:
        multiplier = float(route.cost_multiplier or 1.0)
        if provider.provider_type == "minimax":
            return round(3.0 * multiplier, 6)
        if provider.provider_type == "openai":
            return round(5.0 * multiplier, 6)
        if provider.provider_type == "anthropic":
            return round(6.0 * multiplier, 6)
        return round(4.5 * multiplier, 6)

    def _calc_cost(self, input_tokens: int, output_tokens: int, cost_per_million: float) -> float:
        total_tokens = max(0, input_tokens + output_tokens)
        return round(total_tokens / 1_000_000 * cost_per_million, 6)

    def _prepare_billing(
        self,
        user_id: int | None,
        total_tokens: int,
        cost_amount: float,
        db: Session,
    ) -> dict:
        default = {
            "can_afford": True,
            "grant_usages": [],
            "balance_cost": cost_amount,
            "balance_before": None,
        }
        if user_id is None:
            return default

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return default

        remaining_tokens = max(0, total_tokens)
        grant_usages: list[dict] = []
        now = datetime.now(timezone.utc)
        grants = (
            db.query(TokenGrant)
            .filter(
                TokenGrant.user_id == user_id,
                TokenGrant.status == "active",
                TokenGrant.quota > TokenGrant.used,
            )
            .all()
        )
        grants.sort(
            key=lambda grant: (
                self._normalize_dt(grant.expires_at) is None,
                self._normalize_dt(grant.expires_at) or datetime.max.replace(tzinfo=timezone.utc),
                self._normalize_dt(grant.created_at) or datetime.min.replace(tzinfo=timezone.utc),
            )
        )

        for grant in grants:
            expires_at = self._normalize_dt(grant.expires_at)
            if expires_at and expires_at <= now:
                continue
            available = max(0, int(grant.quota - grant.used))
            if available <= 0 or remaining_tokens <= 0:
                continue
            consume = min(available, remaining_tokens)
            grant_usages.append({"grant_id": grant.id, "tokens": consume})
            remaining_tokens -= consume
            if remaining_tokens <= 0:
                break

        balance_cost = 0.0
        if total_tokens > 0 and remaining_tokens > 0:
            balance_cost = round(cost_amount * remaining_tokens / total_tokens, 6)
        elif total_tokens == 0:
            balance_cost = round(cost_amount, 6)

        can_afford = Decimal(str(user.available_balance or 0)) >= Decimal(str(balance_cost))
        return {
            "can_afford": can_afford,
            "grant_usages": grant_usages,
            "balance_cost": balance_cost,
            "balance_before": float(user.available_balance or 0),
        }

    def _resolve_effective_usage_api_key_id(
        self,
        user_id: int | None,
        user_api_key_id: int | None,
        db: Session,
    ) -> int | None:
        if user_api_key_id is not None:
            return user_api_key_id
        if user_id is None:
            return None
        key = key_service.get_first_active_key(user_id, db)
        if key is not None:
            return key.id
        from app.schemas.api_key import APIKeyCreate

        auto_key = key_service.create_key(
            user_id,
            APIKeyCreate(name="Default Proxy Key", group_name="system"),
            db,
        )
        return auto_key.id

    def _charge_user(
        self,
        user_id: int,
        api_key_id: int,
        public_model_name: str,
        upstream_model_name: str,
        provider_id: int,
        provider_key_id: int,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cost_amount: float,
        latency_ms: int,
        db: Session,
        billing_info: dict,
    ) -> None:
        from app.schemas.account import UsageRecordCreate

        for item in billing_info.get("grant_usages", []):
            grant = db.query(TokenGrant).filter(TokenGrant.id == item["grant_id"]).first()
            if not grant:
                continue
            grant.used += item["tokens"]
            if grant.used >= grant.quota:
                grant.status = "exhausted"

        usage_data = UsageRecordCreate(
            api_key_id=api_key_id,
            model_name=public_model_name,
            public_model_name=public_model_name,
            provider_id=provider_id,
            provider_key_id=provider_key_id,
            upstream_model_name=upstream_model_name,
            request_status="success",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=billing_info.get("balance_cost", 0.0),
            cost_amount=cost_amount,
            latency_ms=latency_ms,
            deduct_balance=billing_info.get("balance_cost", 0.0) > 0,
        )
        usage_service.record(user_id, usage_data, db)

    def _touch_platform_api_key(self, api_key_id: int | None, public_model: str, db: Session) -> None:
        if api_key_id is None:
            return
        api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
        if not api_key:
            return
        api_key.last_used_at = datetime.now(timezone.utc)
        api_key.last_used_model = public_model
        db.commit()

    def _update_provider_key_stats(self, provider_key_rec: ProviderKey, db: Session, error: str | None) -> None:
        provider_key_rec.used_count_today += 1
        provider_key_rec.last_used_at = datetime.now(timezone.utc)
        provider_key_rec.last_error = error
        db.commit()

    def _write_proxy_log(
        self,
        db: Session,
        user_id: int | None,
        user_api_key_id: int | None,
        public_model: str,
        provider_id: int | None,
        provider_name: str | None,
        provider_key_id: int | None,
        upstream_model: str,
        status: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        latency_ms: int,
        error_message: str | None,
        request_id: str | None,
        policy_type: str,
        fallback_triggered: bool,
        provider_switch_count: int,
        key_switch_count: int,
        failure_chain_summary: str,
    ) -> None:
        proxy_log_service.write(
            user_id=user_id,
            user_api_key_id=user_api_key_id,
            public_model=public_model,
            provider_id=provider_id,
            provider_key_id=provider_key_id,
            provider_model_name=upstream_model,
            status=status,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            latency_ms=latency_ms,
            error_message=error_message,
            request_id=request_id,
            db=db,
            upstream_provider_id=provider_id,
            upstream_key_id=provider_key_id,
            policy_type=policy_type,
            fallback_triggered=fallback_triggered,
            retry_attempt=0,
            provider_switch_count=provider_switch_count,
            key_switch_count=key_switch_count,
            failure_chain_summary=failure_chain_summary,
        )

    def _sanitize_error_message(self, message: str) -> str:
        sanitized = message.replace("Bearer ", "").replace("sk-", "key-")
        return sanitized[:240]

    def _summarize_failures(self, failures: list[dict]) -> str:
        if not failures:
            return ""
        parts = []
        for failure in failures[-6:]:
            provider_id = failure.get("provider_id")
            key_id = failure.get("key_id")
            error = str(failure.get("error", ""))[:50]
            parts.append(f"p{provider_id}k{key_id}:{error}")
        return "; ".join(parts)

    def _to_openai_response(
        self,
        upstream_resp: "UpstreamResponse",
        public_model: str,
        debug_data: Optional[dict] = None,
    ) -> dict:
        result = {
            "id": upstream_resp.id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": public_model,
            "choices": upstream_resp.choices,
            "usage": upstream_resp.usage.to_dict(),
        }
        if debug_data:
            result["debug"] = debug_data
        return result


proxy_gateway_service = ProxyGatewayService()
