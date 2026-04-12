from datetime import datetime
from pydantic import BaseModel


class APIKeyCreate(BaseModel):
    name: str
    group_name: str = "default"
    allowed_models: str | None = None
    expires_at: datetime | None = None


class APIKeyUpdate(BaseModel):
    name: str | None = None
    group_name: str | None = None
    status: str | None = None
    allowed_models: str | None = None
    expires_at: datetime | None = None


class APIKeyRead(BaseModel):
    id: int
    name: str
    key_value: str
    group_name: str
    status: str
    expires_at: datetime | None
    allowed_models: str | None
    last_used_at: datetime | None
    last_used_model: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
