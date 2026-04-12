"""
Provider Adapters — 统一适配层。
"""

from app.services.providers.base import (
    BaseAdapter,
    UpstreamRequest,
    UpstreamResponse,
    NormalizedUsage,
    UpstreamError,
)
from app.services.providers.minimax_adapter import MinimaxAdapter

__all__ = [
    "BaseAdapter",
    "UpstreamRequest",
    "UpstreamResponse",
    "NormalizedUsage",
    "UpstreamError",
    "MinimaxAdapter",
]
