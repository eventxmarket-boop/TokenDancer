from pydantic import BaseModel


class PaymentConfigPublic(BaseModel):
    payment_mode: str
    default_currency: str
    alipay_display_name: str
    alipay_qr_image_url: str
    alipay_qr_target_url: str
    alipay_note: str
    enabled_payment_methods: list[str]
    default_payment_method: str
    alipay_qr_mode: str


class PaymentConfigAdmin(BaseModel):
    payment_mode: str = "alipay_qr"
    default_currency: str = "CNY"
    is_enabled: bool = True
    alipay_display_name: str = "支付宝扫码支付"
    alipay_qr_image_url: str = ""
    alipay_qr_target_url: str = ""
    alipay_note: str = ""
    enabled_payment_methods: str | list[str] = "alipay_qr"
    default_payment_method: str = "alipay_qr"
    alipay_qr_mode: str = "universal_static"
