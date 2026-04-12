from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.admin_user import AdminUserRead, AdminUserUpdate


class AdminUserService:
    def list_users(self, db: Session) -> list[AdminUserRead]:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return [AdminUserRead.model_validate(u) for u in users]

    def get_user(self, user_id: int, db: Session) -> AdminUserRead | None:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return AdminUserRead.model_validate(user)

    def update_user(self, user_id: int, data: AdminUserUpdate, db: Session) -> AdminUserRead | None:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        if data.status is not None:
            user.status = data.status
        if data.role is not None:
            user.role = data.role
        if data.balance is not None:
            new_balance = Decimal(str(data.balance))
            user.balance = new_balance
            user.available_balance = new_balance
        db.commit()
        db.refresh(user)
        return AdminUserRead.model_validate(user)


admin_user_service = AdminUserService()
