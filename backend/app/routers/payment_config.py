import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.deps import get_db
from app.schemas.payment_config import PaymentConfigPublic
from app.services.payment_config_service import PaymentConfigService

router = APIRouter(tags=["payment-config"])


@router.get("/payment-config/public", response_model=PaymentConfigPublic)
def get_public_config(db: Session = Depends(get_db)):
    cfg = PaymentConfigService.get_config(db)
    enabled = []
    raw = cfg.enabled_payment_methods or ""
    if raw:
        try:
            enabled = json.loads(raw)
        except Exception:
            enabled = [m.strip() for m in raw.split(",") if m.strip()]
    if not enabled:
        enabled = ["alipay_qr"]
    return PaymentConfigPublic(
        payment_mode=cfg.payment_mode,
        default_currency=cfg.default_currency,
        alipay_display_name=cfg.alipay_display_name,
        alipay_qr_image_url=cfg.alipay_qr_image_url,
        alipay_qr_target_url=cfg.alipay_qr_target_url or "",
        alipay_note=cfg.alipay_note or "",
        enabled_payment_methods=enabled,
        default_payment_method=cfg.default_payment_method,
        alipay_qr_mode=getattr(cfg, "alipay_qr_mode", "universal_static"),
    )
