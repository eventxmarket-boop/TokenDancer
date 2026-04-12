from pydantic import BaseModel


class ProfileRead(BaseModel):
    id: int
    username: str
    email: str
    status: str
    role: str
    balance: float
    available_balance: float

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    username: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
