import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.deps import get_current_user, get_db, rate_limit
from app.models.order import Order
from app.models.payment_event_log import PaymentEventLog
from app.models.user import User
from app.schemas.payment import PaymentIntentCreate, PaymentIntentResponse, PaymentStatus
from app.services.email_service import email_service
from app.services.order_service import OrderService
from app.services.payment_config_service import PaymentConfigService
from app.services.payment_service import StripeProvider, payment_provider

router = APIRouter(prefix="/payments", tags=["payments"])
logger = get_logger(__name__)

SUCCESS_EVENT_TYPES = {
    "payment_intent.succeeded",
    "checkout.session.completed",
    "payment.succeeded",
    "trade_success",
}
SUCCESS_STATUSES = {"succeeded", "success", "paid", "trade_success"}


def _safe_int(value) -> int | None:
    try:
        return int(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None


def _verification_failed(body: bytes, x_webhook_secret: str | None, stripe_signature: str | None) -> tuple[bool, str]:
    payment_secret = (settings.PAYMENT_WEBHOOK_SECRET or "").strip()
    stripe_secret = (settings.STRIPE_WEBHOOK_SECRET or "").strip()

    if stripe_signature and stripe_secret:
        if StripeProvider().verify_webhook(body, stripe_signature):
            return False, "passed"
        return True, "failed"

    if payment_secret:
        if x_webhook_secret == payment_secret:
            return False, "passed"
        return True, "failed"

    return True, "missing_secret"


def _create_event_log(db: Session, payload: dict, verify_result: str) -> PaymentEventLog:
    payment_id = payload.get("payment_id") or payload.get("id", "")
    event_log = PaymentEventLog(
        event_id=payment_id,
        provider=payload.get("provider", "custom"),
        order_id=_safe_int(payload.get("order_id")),
        payment_id=payment_id,
        event_type=payload.get("event_type") or payload.get("status") or "unknown",
        verify_result=verify_result,
        processed=False,
    )
    db.add(event_log)
    db.commit()
    db.refresh(event_log)
    return event_log


def _set_event_log_result(db: Session, event_log_id: int | None, result: str, error_message: str | None = None) -> None:
    if event_log_id is None:
        return
    log = db.query(PaymentEventLog).filter(PaymentEventLog.id == event_log_id).first()
    if not log:
        return
    log.processed = True
    log.processed_result = result
    log.error_message = error_message
    db.commit()


def _send_paid_email(order: Order) -> None:
    if not order.user:
        return
    email_service.send_order_paid(order.user.email, order.user.username, order.order_no)


def _process_paid_order(order_id: int, payment_id: str | None, event_log_id: int | None = None) -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            _set_event_log_result(db, event_log_id, "order_not_found", "order not found")
            return

        if order.status == "paid":
            _set_event_log_result(db, event_log_id, "already_paid")
            return

        if payment_id:
            order.payment_id = payment_id
            db.commit()

        OrderService().fulfill_order(order_id, db)
        db.refresh(order)
        _send_paid_email(order)
        _set_event_log_result(db, event_log_id, "fulfilled")
    except Exception as exc:
        logger.exception(f"Payment fulfillment failed for order {order_id}")
        _set_event_log_result(db, event_log_id, "error", str(exc))
    finally:
        db.close()


@router.post("/create", response_model=PaymentIntentResponse)
def create_payment(
    data: PaymentIntentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此订单")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"订单状态不是 pending（当前：{order.status}），无法创建支付")
    if float(order.total_amount) <= 0:
        raise HTTPException(status_code=400, detail="订单金额为 0，无需支付")

    cfg = PaymentConfigService.get_config(db)
    enabled_methods = PaymentConfigService.get_enabled_methods(cfg)
    if not cfg.is_enabled:
        raise HTTPException(status_code=409, detail="支付功能当前已关闭")
    if data.payment_method not in enabled_methods:
        raise HTTPException(status_code=409, detail=f"支付方式 {data.payment_method} 当前未开放，请选择其他方式")

    order.payment_method = data.payment_method
    db.commit()

    if data.payment_method == "alipay_qr":
        if not cfg.alipay_qr_image_url:
            raise HTTPException(status_code=409, detail="支付宝支付尚未配置收款二维码")
        if not order.payment_id:
            order.payment_id = f"alipay_qr_{order.id}_{int(datetime.now(timezone.utc).timestamp())}"
            db.commit()
        return PaymentIntentResponse(
            payment_id=order.payment_id,
            order_id=order.id,
            amount=float(order.total_amount),
            currency=cfg.default_currency or "CNY",
            status="pending",
            payment_url=f"/shop/alipay-qr?order_id={order.id}",
            created_at=datetime.now(timezone.utc),
        )

    try:
        result = payment_provider.create_payment_intent(
            order_id=data.order_id,
            amount=float(order.total_amount),
            currency=cfg.default_currency or "CNY",
            db=db,
        )
        logger.info(f"Payment created for order {data.order_id} by user {current_user.id}")
        return result
    except Exception as exc:
        logger.exception(f"Payment method {data.payment_method} failed for order {data.order_id}")
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str | None = Header(None, alias="X-Webhook-Secret"),
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    rate_limit(f"webhook:{client_ip}", settings.RATE_LIMIT_WEBHOOK)

    body = await request.body()
    try:
        payload = json.loads(body)
    except Exception:
        logger.error("Webhook: failed to parse JSON body")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    failed, verify_result = _verification_failed(body, x_webhook_secret, stripe_signature)
    event_log = _create_event_log(db, payload, verify_result)

    if failed:
        logger.warning(f"Webhook unauthorized from {client_ip} verify_result={verify_result}")
        _set_event_log_result(db, event_log.id, verify_result, "webhook verification failed")
        raise HTTPException(status_code=401, detail="Webhook 认证失败")

    payment_id = payload.get("payment_id") or payload.get("id", "")
    event_type = str(payload.get("event_type", "")).strip().lower()
    order_id = _safe_int(payload.get("order_id"))
    status = str(payload.get("status", "")).strip().lower()
    provider = payload.get("provider", "custom")

    logger.info(f"Webhook: event={event_type} payment={payment_id} order={order_id} status={status}")

    duplicate = (
        db.query(PaymentEventLog)
        .filter(
            PaymentEventLog.id != event_log.id,
            PaymentEventLog.event_id == payment_id,
            PaymentEventLog.provider == provider,
            PaymentEventLog.processed.is_(True),
            PaymentEventLog.processed_result.in_(["fulfilled", "already_paid"]),
        )
        .first()
    )
    if duplicate:
        _set_event_log_result(db, event_log.id, "already_paid", "duplicate webhook event")
        return {"received": True}

    is_success = event_type in SUCCESS_EVENT_TYPES or status in SUCCESS_STATUSES
    if not is_success:
        _set_event_log_result(db, event_log.id, "ignored")
        return {"received": True}

    if not order_id:
        _set_event_log_result(db, event_log.id, "error", "missing order_id")
        return {"received": True}

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        _set_event_log_result(db, event_log.id, "order_not_found")
        return {"received": True}

    if order.status == "paid":
        _set_event_log_result(db, event_log.id, "already_paid")
        return {"received": True}

    background_tasks.add_task(_process_paid_order, order.id, payment_id, event_log.id)
    return {"received": True}


@router.get("/{order_id}/status", response_model=PaymentStatus)
def get_payment_status(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此订单")

    return PaymentStatus(
        order_id=order.id,
        payment_id=order.payment_id,
        status=order.status,
        paid_at=order.updated_at if order.status == "paid" else None,
    )
