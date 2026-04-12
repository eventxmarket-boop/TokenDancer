from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_admin
from app.models.user import User
from app.models.payment_event_log import PaymentEventLog

router = APIRouter(prefix="/admin/payment-events", tags=["admin-payment-events"])


@router.get("/")
def list_payment_events(
    provider: str = Query(None, description="支付渠道，如 stripe/alipay/wxpay"),
    processed_result: str = Query(None, description="处理结果，如 fulfilled/already_paid/order_not_found/error"),
    verify_result: str = Query(None, description="验签结果，如 passed/failed/missing_secret"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    查询支付事件日志。
    支持按 provider / processed_result / verify_result 筛选。
    """
    q = db.query(PaymentEventLog)
    if provider:
        q = q.filter(PaymentEventLog.provider == provider)
    if processed_result:
        q = q.filter(PaymentEventLog.processed_result == processed_result)
    if verify_result:
        q = q.filter(PaymentEventLog.verify_result == verify_result)

    total = q.count()
    records = (
        q.order_by(PaymentEventLog.received_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "records": records}
