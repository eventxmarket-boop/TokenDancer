from sqlalchemy.orm import Session
from app.models.usage import UsageRecord
from app.schemas.usage import UsageRecordRead
from app.schemas.account import UsageRecordCreate, UsageRecordRead as AccountUsageRead
from app.services.account_service import account_service
from app.core.datetime_utils import parse_date_range


class UsageService:
    def query(
        self,
        user_id: int,
        db: Session,
        api_key_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[UsageRecordRead]:
        # 解析日期
        start, end = None, None
        if date_from or date_to:
            start, end = parse_date_range(date_from, date_to)

        q = db.query(UsageRecord).filter(UsageRecord.user_id == user_id)

        if api_key_id is not None:
            q = q.filter(UsageRecord.api_key_id == api_key_id)

        if start is not None:
            q = q.filter(UsageRecord.requested_at >= start)

        if end is not None:
            q = q.filter(UsageRecord.requested_at <= end)

        records = q.order_by(UsageRecord.requested_at.desc()).all()
        return [UsageRecordRead.model_validate(r) for r in records]

    def record(
        self,
        user_id: int,
        data: UsageRecordCreate,
        db: Session,
    ) -> AccountUsageRead:
        """
        内部接口：写入一条 usage record，并可选扣减账户余额。
        外部 API 代理层（如 Claude/OpenAI 代理）在转发请求后调用此方法。
        """
        return account_service.record_usage(user_id, data, db)


usage_service = UsageService()
