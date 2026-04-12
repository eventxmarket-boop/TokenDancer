from datetime import datetime
from pydantic import BaseModel


class AdminUserRead(BaseModel):
    id: int
    username: str
    email: str
    status: str
    role: str
    balance: float
    available_balance: float
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    status: str | None = None
    role: str | None = None
    balance: float | None = None
