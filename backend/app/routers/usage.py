from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.usage import UsageRecordRead
from app.schemas.account import UsageRecordCreate
from app.services.usage_service import usage_service

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=list[UsageRecordRead])
def query_usage(
    api_key_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    查询当前用户的用量记录。
    支持按 key、时间范围筛选。
    """
    try:
        return usage_service.query(current_user.id, db, api_key_id, date_from, date_to)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("", response_model=UsageRecordRead)
def record_usage(
    data: UsageRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    写入一条用量记录（供内部/代理层调用）。

    外部 API 代理在转发用户请求后，调用此接口记录实际用量并扣费。

    - **api_key_id**: 使用的 API Key ID
    - **model_name**: 模型名称，如 'claude-sonnet-4-20250514'
    - **input_tokens / output_tokens / total_tokens**: token 统计
    - **cost**: 费用（美元）
    - **latency_ms**: 响应延迟
    - **deduct_balance**: 是否真实扣费（测试时可传 false）
    """
    try:
        return usage_service.record(current_user.id, data, db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
