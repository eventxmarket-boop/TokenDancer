from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    status: str
    role: str
    balance: float
    available_balance: float
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
