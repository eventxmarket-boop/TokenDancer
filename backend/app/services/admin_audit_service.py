import json
from sqlalchemy.orm import Session
from app.models.admin_audit_log import AdminAuditLog


class AdminAuditService:

    def log(
        self,
        db: Session,
        action: str,
        admin_user_id: int | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        before_state: dict | None = None,
        after_state: dict | None = None,
        ip_address: str | None = None,
    ):
        """
        记录管理员操作审计日志。

        接入位置（待逐个接入）：
        - admin_provider_keys.py: create / update / delete provider_key
        - admin.py: PATCH /users/{user_id} (role/balance/status 变更)
        - admin.py: PATCH /orders/{order_id} (status 变更)
        - admin.py: POST/DELETE /redeem-codes
        """
        log = AdminAuditLog(
            admin_user_id=admin_user_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            before_state=json.dumps(before_state) if before_state else None,
            after_state=json.dumps(after_state) if after_state else None,
            ip_address=ip_address,
        )
        db.add(log)
        db.commit()


admin_audit_service = AdminAuditService()
