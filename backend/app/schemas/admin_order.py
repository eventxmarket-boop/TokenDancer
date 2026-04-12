from pydantic import BaseModel


class AdminOrderUpdate(BaseModel):
    status: str | None = None
