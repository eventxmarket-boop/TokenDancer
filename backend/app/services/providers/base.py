"""
Provider Adapter 抽象层。
定义 BaseAdapter 协议，所有 upstream adapter 必须实现。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class UpstreamRequest:
    """统一的上游请求结构。"""
    model: str                          # 上游实际模型名
    messages: list[dict]                # [{role, content}, ...]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


@dataclass
class UpstreamResponse:
    """统一的上游响应结构。"""
    id: str
    model: str
    choices: list[dict]                # OpenAI 格式 choices
    usage: "NormalizedUsage"
    raw: dict = field(default_factory=dict)  # 原始响应体


@dataclass
class NormalizedUsage:
    """归一化后的 usage。"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class UpstreamError:
    """归一化后的上游错误。"""
    code: str                           # upstream_timeout | upstream_auth | upstream_server | upstream_unknown
    message: str
    status_code: Optional[int] = None  # HTTP status code if applicable


class BaseAdapter(ABC):
    """
    Provider Adapter 协议。
    所有 provider adapter 必须实现以下方法。
    """

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """返回 provider 类型标识符，如 'minimax'、'openai' 等。"""
        ...

    @abstractmethod
    async def call(
        self,
        api_key: str,
        request: UpstreamRequest,
        timeout: float = 60.0,
    ) -> UpstreamResponse:
        """
        发送请求到上游，返回归一化响应。
        内部自行处理错误归类。
        """
        ...

    @abstractmethod
    def parse_error(self, exc: Exception, raw_response: Optional[dict] = None) -> UpstreamError:
        """
        将异常解析为 UpstreamError。
        exc: httpx.HTTPStatusError / httpx.TimeoutException / 其他
        raw_response: 原始响应体（如有）
        """
        ...
