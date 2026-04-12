from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_admin
from app.models.admin_audit_log import AdminAuditLog
from app.models.user import User

router = APIRouter(prefix="/admin/audit-logs", tags=["admin-audit-logs"])


@router.get("/")
def list_audit_logs(
    admin_user_id: int = Query(None, description="按管理员用户ID筛选"),
    action: str = Query(None, description="按操作类型筛选，如 provider_key.create"),
    target_type: str = Query(None, description="按目标类型筛选，如 provider_key / user / order"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    查询管理员操作审计日志。
    支持按 admin_user_id / action / target_type 筛选，支持分页。
    """
    q = db.query(AdminAuditLog)
    if admin_user_id is not None:
        q = q.filter(AdminAuditLog.admin_user_id == admin_user_id)
    if action:
        q = q.filter(AdminAuditLog.action == action)
    if target_type:
        q = q.filter(AdminAuditLog.target_type == target_type)

    total = q.count()
    records = (
        q.order_by(AdminAuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # 序列化：JSON 字符串的 before_state / after_state 保持为字符串返回
    return {
        "total": total,
        "records": [
            {
                "id": r.id,
                "admin_user_id": r.admin_user_id,
                "action": r.action,
                "target_type": r.target_type,
                "target_id": r.target_id,
                "before_state": r.before_state,
                "after_state": r.after_state,
                "ip_address": r.ip_address,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }
