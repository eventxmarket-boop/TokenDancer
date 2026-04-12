from datetime import datetime
from app.models import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    plan_name = Column(String(200), nullable=False)          # 套餐名称
    status = Column(String(20), default="active")            # active | expired | cancelled
    starts_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    source_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
