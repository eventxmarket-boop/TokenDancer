from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password, hash_password


class ProfileService:
    def get_profile(self, user: User) -> dict:
        return {
            "username": user.username,
            "email": user.email,
            "status": user.status,
            "balance": float(user.balance),
            "available_balance": float(user.available_balance),
            "created_at": user.created_at,
        }

    def update_profile(self, user: User, data: dict, db: Session) -> dict:
        if "username" in data and data["username"]:
            user.username = data["username"]
        db.commit()
        db.refresh(user)
        return self.get_profile(user)

    def change_password(
        self, user: User, current_password: str, new_password: str, db: Session
    ) -> dict:
        if not verify_password(current_password, user.password_hash):
            raise ValueError("当前密码不正确")
        if len(new_password) < 8:
            raise ValueError("新密码长度不能少于 8 位")
        user.password_hash = hash_password(new_password)
        db.commit()
        return {"ok": True, "message": "密码修改成功"}


profile_service = ProfileService()
