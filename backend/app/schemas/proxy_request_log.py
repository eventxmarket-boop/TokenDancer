from datetime import datetime
from pydantic import BaseModel


class ProxyRequestLogRead(BaseModel):
    id: int
    request_id: str | None
    user_id: int | None
    user_api_key_id: int | None
    public_model_name: str
    provider_id: int | None
    provider_key_id: int | None
    provider_model_name: str
    request_status: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    latency_ms: int
    error_message: str | None
    requested_at: datetime
    # v4.0.0 扩展字段
    upstream_provider_id: int | None = None
    upstream_key_id: int | None = None
    policy_type: str = "fixed"
    fallback_triggered: bool = False
    retry_attempt: int = 0
    provider_switch_count: int = 0
    key_switch_count: int = 0
    failure_chain_summary: str | None = None

    model_config = {"from_attributes": True}


class ProxyRequestLogFilter(BaseModel):
    provider_id: int | None = None
    public_model_name: str | None = None
    request_status: str | None = None
    date_from: str | None = None
    date_to: str | None = None
