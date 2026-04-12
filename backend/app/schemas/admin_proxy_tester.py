from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AdminProxyTesterMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1)


class AdminProxyTesterRequest(BaseModel):
    public_model_name: str = Field(..., min_length=1)
    route_mode: Literal["auto", "provider", "provider_key"] = "auto"
    provider_id: int | None = None
    provider_key_id: int | None = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=512, ge=1, le=8192)
    stream: bool = False
    messages: list[AdminProxyTesterMessage] = Field(default_factory=list, min_length=1)

    @model_validator(mode="after")
    def validate_route_selection(self):
        if self.route_mode == "provider" and not self.provider_id:
            raise ValueError("指定 Provider 模式下必须选择 Provider")
        if self.route_mode == "provider_key" and not self.provider_key_id:
            raise ValueError("指定 Source Key 模式下必须选择 Source Key")
        return self


class AdminProxyTesterOptionsResponse(BaseModel):
    models: list[dict]
    providers: list[dict]
    provider_keys: list[dict]
    route_policies: list[dict]


class AdminProxyTesterResponse(BaseModel):
    success: bool
    status_code: int
    route_mode: Literal["auto", "provider", "provider_key"]
    public_model_name: str
    assistant_message: str | None = None
    error_summary: str | None = None
    request_id: str | None = None
    request_log_id: int | None = None
    request_origin: str = "admin_tester"
    request_tag: str | None = None
    request_status: str | None = None
    latency_ms: float | None = None
    provider_id: int | None = None
    provider_name: str | None = None
    provider_type: str | None = None
    provider_key_id: int | None = None
    provider_key_name: str | None = None
    policy_name: str | None = None
    policy_type: str | None = None
    upstream_model_name: str | None = None
    fallback_triggered: bool = False
    provider_switch_count: int = 0
    key_switch_count: int = 0
    failure_chain_summary: str | None = None
    log_written: bool = False
    source_key_usage_updated: bool = False
    source_key_last_used_at: datetime | None = None
    source_key_used_count_today: int | None = None
    forced_provider_honored: bool | None = None
    forced_source_key_honored: bool | None = None
    usage: dict | None = None
