from datetime import datetime
from app.models import Base
from sqlalchemy import Column, Integer, String, Text, DateTime

class ContentPage(Base):
    __tablename__ = "content_pages"

    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, nullable=False)  # "privacy" | "terms"
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
