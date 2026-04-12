"""
Proxy 层自定义异常定义。

所有 proxy 业务异常从此定义，router 层统一映射为 HTTPException。
异常信息对外部安全（不暴露内部栈），详细原因写 logger。
"""

from fastapi import HTTPException


class ProxyBaseException(Exception):
    """Proxy 层异常基类。"""

    def __init__(self, message: str, internal_detail: str | None = None):
        self.message = message
        self.internal_detail = internal_detail or message
        super().__init__(self.message)

    def to_http(self, status_code: int) -> HTTPException:
        return HTTPException(status_code=status_code, detail=self.message)


class ModelRouteNotFoundError(ProxyBaseException):
    """404 - 请求的 public_model 在 ModelRoute 表中不存在。"""

    def __init__(self, public_model: str):
        super().__init__(
            message=f"Model not found: {public_model}",
            internal_detail=f"No ModelRoute for public_model={public_model}",
        )

    def to_http(self):
        return super().to_http(404)


class RoutePolicyNotFoundError(ProxyBaseException):
    """404 - 该 model 没有关联的 RoutePolicy。"""

    def __init__(self, public_model: str):
        super().__init__(
            message="Route policy not configured",
            internal_detail=f"No RoutePolicy for public_model={public_model}",
        )

    def to_http(self):
        return super().to_http(404)


class NoAvailableProviderError(ProxyBaseException):
    """409 - 该路由没有可用（active 且非 cooldown）的 provider。"""

    def __init__(self, public_model: str, reason: str = ""):
        super().__init__(
            message="No available provider for this model",
            internal_detail=f"NoAvailableProviderError for {public_model}: {reason}",
        )

    def to_http(self):
        return super().to_http(409)


class NoAvailableProviderKeyError(ProxyBaseException):
    """409 - 该 provider 没有可用的（active）key。"""

    def __init__(self, provider_name: str):
        super().__init__(
            message="No available API key for provider",
            internal_detail=f"No active ProviderKey for provider={provider_name}",
        )

    def to_http(self):
        return super().to_http(409)


class UpstreamTimeoutError(ProxyBaseException):
    """504 - 上游 provider 请求超时。"""

    def __init__(self, provider_name: str, timeout_seconds: float):
        super().__init__(
            message="Upstream request timeout",
            internal_detail=f"UpstreamTimeout: provider={provider_name}, timeout={timeout_seconds}s",
        )

    def to_http(self):
        return super().to_http(504)


class UpstreamAuthError(ProxyBaseException):
    """401 / 502 - 上游认证失败（key 无效/过期）。"""

    def __init__(self, provider_name: str):
        super().__init__(
            message="Upstream authentication failed",
            internal_detail=f"UpstreamAuthError: provider={provider_name} (invalid or expired API key)",
        )

    def to_http(self):
        return super().to_http(401)


class UpstreamServerError(ProxyBaseException):
    """502 - 上游 provider 返回 5xx。"""

    def __init__(self, provider_name: str, status_code: int):
        super().__init__(
            message="Upstream server error",
            internal_detail=f"UpstreamServerError: provider={provider_name}, status={status_code}",
        )

    def to_http(self):
        return super().to_http(502)


class AllRetriesFailedError(ProxyBaseException):
    """502 - 所有重试均失败（主 + fallback provider 均不可用）。"""

    def __init__(self, public_model: str, last_error: str):
        super().__init__(
            message="All providers failed, please try again later",
            internal_detail=f"AllRetriesFailed for {public_model}, last_error={last_error}",
        )

    def to_http(self):
        return super().to_http(502)


class ProviderUnavailableError(ProxyBaseException):
    """409 - 指定 provider 不可用（被过滤或无健康 key）。"""

    def __init__(self, provider_name: str, reason: str = ""):
        super().__init__(
            message=f"Provider unavailable: {provider_name}",
            internal_detail=f"ProviderUnavailableError provider={provider_name}: {reason}",
        )

    def to_http(self):
        return super().to_http(409)


class AllProvidersFailedError(ProxyBaseException):
    """502 - 所有 provider（含 fallback）均失败。"""

    def __init__(self, public_model: str, last_error: str, failures: list[dict] | None = None):
        detail = f"AllProvidersFailed for {public_model}, last_error={last_error}"
        if failures:
            import json
            detail += f", failures={json.dumps(failures, ensure_ascii=False)}"
        super().__init__(
            message="All providers exhausted, please try again later",
            internal_detail=detail,
        )

    def to_http(self):
        return super().to_http(502)


class AllProviderKeysFailedError(ProxyBaseException):
    """
    409 - 同 Provider 下所有 Key 均失败，且所有 Provider 也均失败。

    第3阶段多Key调度专用异常，携带详细失败链供日志分析：
    - failures: [{"key_id": int, "error": str}, ...]
    """

    def __init__(
        self,
        public_model: str,
        last_error: str,
        failures: list[dict] | None = None,
    ):
        self.failures = failures or []
        detail = (
            f"AllProviderKeysFailed for {public_model}, "
            f"last_error={last_error}, failed_keys={self.failures}"
        )
        super().__init__(
            message="All API keys failed, please try again later",
            internal_detail=detail,
        )

    def to_http(self):
        return super().to_http(409)


class KeyDecryptionError(ProxyBaseException):
    """500 - provider key 解密失败。"""

    def __init__(self, key_id: int):
        super().__init__(
            message="Internal key error",
            internal_detail=f"Failed to decrypt ProviderKey id={key_id}",
        )

    def to_http(self):
        return super().to_http(500)


class RateLimitError(ProxyBaseException):
    """429 - 用户触发限流。"""

    def __init__(self):
        super().__init__(
            message="Rate limit exceeded",
            internal_detail="User triggered rate limit on proxy endpoint",
        )

    def to_http(self):
        return super().to_http(429)


class InsufficientBalanceError(ProxyBaseException):
    """402 - 用户余额/配额不足，无法发起请求。"""

    def __init__(self):
        super().__init__(
            message="Insufficient balance or token quota",
            internal_detail="User has insufficient balance or TokenGrant quota to proceed with this request",
        )

    def to_http(self):
        return super().to_http(402)
