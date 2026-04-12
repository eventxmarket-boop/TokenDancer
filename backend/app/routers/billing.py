from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models.user import User
from app.services.account_service import account_service

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/summary")
def get_billing_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户账单概览"""
    account = account_service.get_or_create_account(current_user.id, db)
    return {
        "balance": float(account.balance),
        "available_balance": float(account.available_balance),
        "user_id": current_user.id,
    }


@router.get("/ledger")
def get_ledger(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户账本流水"""
    ledger = account_service.list_ledger(current_user.id, db, limit=50)
    return [
        {
            "id": entry.id,
            "type": entry.operation,
            "operation": entry.operation,
            "amount": float(entry.amount),
            "balance_after": float(entry.balance_after),
            "remark": entry.remark,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }
        for entry in ledger
    ]
