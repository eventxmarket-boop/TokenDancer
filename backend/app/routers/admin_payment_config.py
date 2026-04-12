from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_admin
from app.models.order import Order
from app.models.payment_event_log import PaymentEventLog
from app.schemas.payment_config import PaymentConfigAdmin
from app.services.order_service import OrderService
from app.services.payment_config_service import PaymentConfigService
from app.core.logging import get_logger

router = APIRouter(prefix="/admin/payment-config", tags=["admin-payment-config"])
logger = get_logger(__name__)


def _build_response(cfg) -> PaymentConfigAdmin:
    return PaymentConfigAdmin(
        payment_mode=cfg.payment_mode,
        default_currency=cfg.default_currency,
        is_enabled=cfg.is_enabled,
        alipay_display_name=cfg.alipay_display_name,
        alipay_qr_image_url=cfg.alipay_qr_image_url,
        alipay_qr_target_url=cfg.alipay_qr_target_url or "",
        alipay_note=cfg.alipay_note or "",
        enabled_payment_methods=cfg.enabled_payment_methods or "alipay_qr",
        default_payment_method=cfg.default_payment_method or "alipay_qr",
        alipay_qr_mode=cfg.alipay_qr_mode or "universal_static",
    )


@router.get("/", response_model=PaymentConfigAdmin)
def get_config(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    cfg = PaymentConfigService.get_config(db)
    return _build_response(cfg)


@router.put("/", response_model=PaymentConfigAdmin)
def update_config(
    data: PaymentConfigAdmin,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    cfg = PaymentConfigService.update_config(db, data.model_dump())
    return _build_response(cfg)


@router.post("/orders/{order_id}/repair")
def repair_order(
    order_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status == "paid":
        return {"success": True, "message": "订单已完成支付，无需补偿"}

    success_event = (
        db.query(PaymentEventLog)
        .filter(
            PaymentEventLog.order_id == order_id,
            PaymentEventLog.verify_result == "passed",
            PaymentEventLog.event_type.in_([
                "payment_intent.succeeded",
                "checkout.session.completed",
                "trade_success",
                "payment.succeeded",
            ]),
        )
        .order_by(PaymentEventLog.received_at.desc())
        .first()
    )

    if not success_event and not order.payment_id:
        raise HTTPException(status_code=409, detail="未发现有效支付凭据，无法执行异常补偿")

    if success_event and success_event.payment_id and not order.payment_id:
        order.payment_id = success_event.payment_id
        db.commit()

    try:
        OrderService().fulfill_order(order.id, db)
        db.refresh(order)
    except Exception as exc:
        logger.exception(f"Payment repair failed for order {order_id}")
        raise HTTPException(status_code=500, detail=f"异常补偿失败: {exc}")

    return {"success": True, "message": "异常补偿完成，订单权益已重新校验并发放", "status": order.status}
