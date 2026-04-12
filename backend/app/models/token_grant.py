from datetime import datetime
from app.models import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger

class TokenGrant(Base):
    __tablename__ = "token_grants"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    quota = Column(BigInteger, default=0)                     # token 配额总量
    used = Column(BigInteger, default=0)                    # 已使用量
    status = Column(String(20), default="active")            # active | exhausted | expired
    source_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    expires_at = Column(DateTime, nullable=True)            # 若不过期则为空
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
