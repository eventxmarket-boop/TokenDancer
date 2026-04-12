from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class AnnouncementCreate(BaseModel):
    title: str
    content: str = ""
    is_active: bool = True
    published_at: Optional[datetime] = None

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None
    published_at: Optional[datetime] = None

class AnnouncementRead(BaseModel):
    id: int
    title: str
    content: str
    is_active: bool
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = {"from_attributes": True}


class PageUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class PageRead(BaseModel):
    id: int
    slug: str
    title: str
    content: str
    updated_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


class QrCreate(BaseModel):
    title: str
    description: str = ""
    image_url: str = ""
    target_url: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

class QrUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    target_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class QrRead(BaseModel):
    id: int
    title: str
    description: str
    image_url: str
    target_url: Optional[str]
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = {"from_attributes": True}
