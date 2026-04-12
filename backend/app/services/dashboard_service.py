from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.api_key import APIKey
from app.models.usage import UsageRecord


class DashboardService:
    def get_summary(self, user_id: int, db: Session) -> dict:
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)

        # Fetch user for real balance
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        # Balance — 来自 User 表的真实字段
        balance = float(user.balance)
        available_balance = float(user.available_balance)

        # API Key 数量
        api_key_count = db.query(func.count(APIKey.id)).filter(
            APIKey.user_id == user_id
        ).scalar() or 0

        # Usage 今日聚合
        today_stats = db.query(
            func.count(UsageRecord.id).label("requests"),
            func.coalesce(func.sum(UsageRecord.cost), 0).label("cost"),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0).label("tokens"),
            func.coalesce(func.avg(UsageRecord.latency_ms), 0).label("latency"),
        ).filter(
            and_(
                UsageRecord.user_id == user_id,
                UsageRecord.requested_at >= today_start,
                UsageRecord.requested_at <= today_end,
            )
        ).first()

        today_requests = int(today_stats.requests) if today_stats else 0
        today_cost = float(today_stats.cost) if today_stats else 0.0
        today_tokens = int(today_stats.tokens) if today_stats else 0
        avg_latency_ms = int(float(today_stats.latency)) if today_stats else 0

        # Usage 全量累计
        total_tokens = db.query(
            func.coalesce(func.sum(UsageRecord.total_tokens), 0)
        ).filter(UsageRecord.user_id == user_id).scalar() or 0

        return {
            "balance": round(balance, 4),
            "available_balance": round(available_balance, 4),
            "api_key_count": api_key_count,
            "today_requests": today_requests,
            "today_cost": round(today_cost, 4),
            "today_tokens": today_tokens,
            "total_tokens": int(total_tokens),
            "rpm": today_requests,
            "tpm": today_tokens,
            "avg_latency_ms": avg_latency_ms,
        }


dashboard_service = DashboardService()
