"""
Provider 健康检查模块。
提供轻量 HTTP 探测判断上游 provider 是否可达。
"""
import httpx
import logging
from typing import Literal

from app.models.provider import Provider

logger = logging.getLogger(__name__)

HealthStatus = Literal["unknown", "healthy", "degraded", "unreachable"]


async def check_provider_health(provider: Provider) -> HealthStatus:
    """
    对 provider.base_url 发一个最小 HEAD/GET 请求，
    判断其是否可达。
    """
    if not provider.base_url:
        return "unknown"

    test_url = provider.base_url.rstrip("/") + "/models"
    timeout = 8.0

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(test_url, follow_redirects=True)
            if resp.status_code < 500:
                return "healthy"
            else:
                return "degraded"
    except httpx.TimeoutException:
        return "unreachable"
    except Exception:
        return "degraded"


def sync_check_provider_health(provider: Provider) -> HealthStatus:
    """同步版本，用于 admin 接口直接调用。"""
    if not provider.base_url:
        return "unknown"

    test_url = provider.base_url.rstrip("/") + "/models"
    timeout = 8.0

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(test_url, follow_redirects=True)
            if resp.status_code < 500:
                return "healthy"
            return "degraded"
    except httpx.TimeoutException:
        return "unreachable"
    except Exception:
        return "degraded"
