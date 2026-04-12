from sqlalchemy import Boolean, Column, Integer, String, Text
from app.core.database import Base


class PaymentConfig(Base):
    __tablename__ = "payment_configs"

    id = Column(Integer, primary_key=True, default=1)
    payment_mode = Column(String(50), default="alipay_qr")
    default_currency = Column(String(10), default="CNY")
    is_enabled = Column(Boolean, default=True)
    alipay_display_name = Column(String(100), default="支付宝扫码支付")
    alipay_qr_image_url = Column(Text, default="")
    alipay_qr_target_url = Column(Text, default="")
    alipay_note = Column(Text, default="请按订单金额完成支付，支付结果将自动同步")
    enabled_payment_methods = Column(String(200), default="alipay_qr")
    default_payment_method = Column(String(50), default="alipay_qr")
    alipay_qr_mode = Column(String(50), default="universal_static")
