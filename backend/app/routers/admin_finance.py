from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.deps import get_db, get_current_admin
from app.models.user import User
from app.models.account import BalanceLedger
from app.models.usage import UsageRecord
from app.services.account_service import account_service

router = APIRouter(prefix="/admin/finance", tags=["admin-finance"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """财务总览：用户数/总余额/总账本记录数等"""
    user_count = db.query(User).count()
    total_balance = db.query(User.balance).all()
    total = sum(float(u.balance or 0) for u in total_balance)
    ledger_count = db.query(BalanceLedger).count()
    usage_count = db.query(UsageRecord).count()
    return {
        "user_count": user_count,
        "total_balance": round(total, 4),
        "ledger_count": ledger_count,
        "usage_count": usage_count,
    }


@router.get("/ledger")
def ledger(
    user_id: Optional[int] = None,
    entry_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """余额账本流水（管理员视角）"""
    q = db.query(BalanceLedger)
    if user_id is not None:
        q = q.filter(BalanceLedger.user_id == user_id)
    if entry_type:
        q = q.filter(BalanceLedger.operation == entry_type)
    total = q.count()
    records = (
        q.order_by(desc(BalanceLedger.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    # 补上用户邮箱
    user_ids = list({r.user_id for r in records})
    users_map = {
        u.id: u.email
        for u in db.query(User).filter(User.id.in_(user_ids)).all()
    }
    return {
        "total": total,
        "records": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "user_email": users_map.get(r.user_id, ""),
                "operation": r.operation,
                "amount": float(r.amount),
                "balance_before": float(r.balance_before),
                "balance_after": float(r.balance_after),
                "redeem_log_id": r.redeem_log_id,
                "usage_record_id": r.usage_record_id,
                "order_id": r.order_id,
                "remark": r.remark,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }


@router.get("/usage")
def usage(
    user_id: Optional[int] = None,
    model: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """API Usage 明细（管理员视角）"""
    q = db.query(UsageRecord)
    if user_id is not None:
        q = q.filter(UsageRecord.user_id == user_id)
    if model:
        q = q.filter(UsageRecord.model_name == model)
    total = q.count()
    records = (
        q.order_by(desc(UsageRecord.requested_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "records": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "api_key_id": r.api_key_id,
                "model_name": r.model_name,
                "public_model_name": r.public_model_name,
                "provider_id": r.provider_id,
                "provider_key_id": r.provider_key_id,
                "upstream_model_name": r.upstream_model_name,
                "request_status": r.request_status,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "total_tokens": r.total_tokens,
                "cost": float(r.cost),
                "cost_amount": float(r.cost_amount or r.cost or 0),
                "latency_ms": r.latency_ms,
                "requested_at": r.requested_at.isoformat() if r.requested_at else None,
            }
            for r in records
        ],
    }
