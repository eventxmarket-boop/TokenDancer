"""
Minimax Provider Adapter。
实现 BaseAdapter 协议，对接 Minimax 官方 /v1/text/chatcompletion_v2 接口。
"""

import httpx
from typing import Any, Optional

from app.services.providers.base import (
    BaseAdapter,
    UpstreamRequest,
    UpstreamResponse,
    NormalizedUsage,
    UpstreamError,
)
from app.core.proxy_errors import (
    InvalidUpstreamModelError,
    UpstreamBadRequestError,
    UpstreamTimeoutError,
    UpstreamAuthError,
    UpstreamServerError,
)


class MinimaxAdapter(BaseAdapter):
    """
    Minimax 官方 API 适配器。

    Minimax API:
        POST https://api.minimax.chat/v1/text/chatcompletion_v2
        Header: Authorization: Bearer <api_key>
        Body: { model, messages, temperature, max_tokens, stream }

    Minimax Usage 响应字段:
        {
            "usage": {
                "prompt_tokens": <int>,
                "completion_tokens": <int>,
                "total_tokens": <int>,
            }
        }
    """

    provider_type: str = "minimax"

    # Minimax 官方 API 端点（可被 base_url 覆盖）
    DEFAULT_BASE_URL: str = "https://api.minimax.chat"

    async def call(
        self,
        api_key: str,
        request: UpstreamRequest,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> UpstreamResponse:
        """
        发送请求到 Minimax 官方 API，返回归一化响应。
        """
        base = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        url = f"{base}/v1/text/chatcompletion_v2"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "stream": request.stream,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                url, json=payload, headers=headers, follow_redirects=True
            )

            if resp.status_code == 401:
                raise UpstreamAuthError("minimax")
            if resp.status_code >= 500:
                raise UpstreamServerError("minimax", resp.status_code)
            if resp.status_code >= 400:
                raise UpstreamBadRequestError("minimax", self._summarize_http_error(resp))

            data = self._safe_json_dict(resp)
            self._raise_if_minimax_error(data, request.model)

        # ── 解析 usage ─────────────────────────────────────────
        raw_usage = data.get("usage") or {}
        if not isinstance(raw_usage, dict):
            raw_usage = {}
        usage = self._normalize_usage(raw_usage)
        choices = data.get("choices") or []
        if not isinstance(choices, list):
            choices = []

        return UpstreamResponse(
            id=data.get("id", "chatcmpl-minimax"),
            model=data.get("model", request.model),
            choices=choices,
            usage=usage,
            raw=data,
        )

    def _safe_json_dict(self, resp: httpx.Response) -> dict[str, Any]:
        try:
            data = resp.json()
        except Exception as exc:
            raise UpstreamBadRequestError("minimax", f"invalid JSON response: {type(exc).__name__}") from exc
        if not isinstance(data, dict):
            raise UpstreamBadRequestError("minimax", "upstream returned non-object JSON")
        return data

    def _summarize_http_error(self, resp: httpx.Response) -> str:
        text = (resp.text or "").strip()
        if not text:
            return f"HTTP {resp.status_code}"
        return f"HTTP {resp.status_code}: {text[:240]}"

    def _raise_if_minimax_error(self, data: dict[str, Any], model_name: str) -> None:
        base_resp = data.get("base_resp")
        if not isinstance(base_resp, dict):
            return

        status_code = base_resp.get("status_code")
        if status_code in (None, 0, "0"):
            return

        status_msg = str(base_resp.get("status_msg") or "").strip() or f"status_code={status_code}"
        lowered = status_msg.lower()
        if "unknown model" in lowered or "invalid model" in lowered:
            raise InvalidUpstreamModelError("minimax", model_name, status_msg)
        if "api key" in lowered or "token" in lowered or "auth" in lowered or "unauthorized" in lowered:
            raise UpstreamAuthError("minimax")
        raise UpstreamBadRequestError("minimax", status_msg)

    def _normalize_usage(self, raw_usage: dict) -> NormalizedUsage:
        """
        Minimax → NormalizedUsage 映射规则：

        Minimax 字段（官方文档）:
            prompt_tokens     → input_tokens
            completion_tokens → output_tokens
            total_tokens      → total_tokens

        兜底：缺失字段取 0，最终 total_tokens = max(传入值, prompt+completion)
        """
        prompt = int(raw_usage.get("prompt_tokens", 0) or 0)
        completion = int(raw_usage.get("completion_tokens", 0) or 0)
        total = int(raw_usage.get("total_tokens", 0) or 0)

        # 兜底：若 total 缺失或不等于前后之和，推断
        if total == 0:
            total = prompt + completion
        elif total != prompt + completion:
            # 以 prompt + completion 为准
            total = prompt + completion

        return NormalizedUsage(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=total,
        )

    def parse_error(self, exc: Exception, raw_response: Optional[dict] = None) -> UpstreamError:
        """
        将 Exception 解析为 UpstreamError。
        """
        if isinstance(exc, httpx.TimeoutException):
            return UpstreamError(
                code="upstream_timeout",
                message="Minimax request timeout",
                status_code=None,
            )
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            if status == 401:
                return UpstreamError(
                    code="upstream_auth",
                    message="Minimax API key invalid or expired",
                    status_code=status,
                )
            return UpstreamError(
                code="upstream_server",
                message=f"Minimax returned HTTP {status}",
                status_code=status,
            )
        if isinstance(exc, UpstreamTimeoutError):
            return UpstreamError(code="upstream_timeout", message=str(exc), status_code=None)
        if isinstance(exc, UpstreamAuthError):
            return UpstreamError(code="upstream_auth", message=str(exc), status_code=401)
        if isinstance(exc, UpstreamServerError):
            return UpstreamError(
                code="upstream_server",
                message=str(exc),
                status_code=exc.internal_detail,
            )
        return UpstreamError(
            code="upstream_unknown",
            message=str(exc),
            status_code=getattr(exc, "status_code", None),
        )

    def build_upstream_request(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: Optional[int],
        stream: bool,
    ) -> UpstreamRequest:
        """构造上游请求对象（供 gateway 调用前使用）。"""
        return UpstreamRequest(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )
