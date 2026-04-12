from datetime import datetime
from app.models import Base
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime

class ContentAnnouncement(Base):
    __tablename__ = "content_announcements"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False, default="")
    is_active = Column(Boolean, default=True)
    published_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
