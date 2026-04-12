from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_admin
from app.models.user import User
from app.schemas.proxy_request_log import ProxyRequestLogRead, ProxyRequestLogFilter
from app.services.proxy_log_service import proxy_log_service

router = APIRouter(prefix="/admin/proxy-logs", tags=["admin-proxy-logs"])


@router.get("", response_model=list[ProxyRequestLogRead])
def list_proxy_logs(
    provider_id: int | None = Query(None),
    public_model_name: str | None = Query(None),
    request_status: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    查询代理请求日志。
    支持按 provider/model/status/时间范围筛选。
    """
    return proxy_log_service.query(
        db,
        provider_id=provider_id,
        public_model_name=public_model_name,
        request_status=request_status,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
