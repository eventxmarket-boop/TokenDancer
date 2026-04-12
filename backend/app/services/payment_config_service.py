from sqlalchemy.orm import Session
from app.models.payment_config import PaymentConfig


class PaymentConfigService:
    @staticmethod
    def get_enabled_methods(cfg: PaymentConfig) -> list[str]:
        raw = cfg.enabled_payment_methods or ""
        if not raw:
            return ["alipay_qr"]
        if isinstance(raw, str):
            raw = raw.strip()
            if raw.startswith("["):
                try:
                    import json
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        methods = [str(m).strip() for m in parsed if str(m).strip()]
                        return methods or ["alipay_qr"]
                except Exception:
                    pass
            methods = [m.strip() for m in raw.split(",") if m.strip()]
            return methods or ["alipay_qr"]
        return ["alipay_qr"]

    @staticmethod
    def _normalize_legacy_values(cfg: PaymentConfig, db: Session) -> PaymentConfig:
        changed = False
        if getattr(cfg, "payment_mode", "") == "manual_qr":
            cfg.payment_mode = "alipay_qr"
            changed = True
        if getattr(cfg, "alipay_qr_mode", "") == "fixed_amount_test":
            cfg.alipay_qr_mode = "universal_static"
            changed = True
        if changed:
            db.commit()
            db.refresh(cfg)
        return cfg

    @staticmethod
    def get_config(db: Session) -> PaymentConfig:
        cfg = db.query(PaymentConfig).filter(PaymentConfig.id == 1).first()
        if not cfg:
            cfg = PaymentConfig(id=1)
            db.add(cfg)
            db.commit()
            db.refresh(cfg)
        return PaymentConfigService._normalize_legacy_values(cfg, db)

    @staticmethod
    def update_config(db: Session, data: dict) -> PaymentConfig:
        cfg = PaymentConfigService.get_config(db)
        for k, v in data.items():
            if not hasattr(cfg, k):
                continue
            if v is None:
                continue
            if k == "enabled_payment_methods":
                if isinstance(v, list):
                    v = ",".join(str(m) for m in v if m)
                elif not isinstance(v, str):
                    v = str(v)
            if k == "payment_mode" and v == "manual_qr":
                v = "alipay_qr"
            if k == "alipay_qr_mode":
                v = "universal_static"
            setattr(cfg, k, v)
        db.commit()
        db.refresh(cfg)
        return cfg
