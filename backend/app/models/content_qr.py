from datetime import datetime
from app.models import Base
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime

class ContentQr(Base):
    __tablename__ = "content_qrs"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    image_url = Column(String(500), default="")
    target_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
