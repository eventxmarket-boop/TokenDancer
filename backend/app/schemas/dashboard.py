from pydantic import BaseModel


class DashboardSummary(BaseModel):
    balance: float = 0.0
    available_balance: float = 0.0
    api_key_count: int = 0
    today_requests: int = 0
    today_cost: float = 0.0
    today_tokens: int = 0
    total_tokens: int = 0
    rpm: int = 0
    tpm: int = 0
    avg_latency_ms: int = 0
