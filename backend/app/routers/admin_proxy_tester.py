from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_admin, get_db
from app.models.user import User
from app.schemas.admin_proxy_tester import (
    AdminProxyTesterOptionsResponse,
    AdminProxyTesterRequest,
    AdminProxyTesterResponse,
)
from app.services.proxy_tester_service import proxy_tester_service

router = APIRouter(prefix="/admin/proxy-tester", tags=["admin-proxy-tester"])


@router.get("/options", response_model=AdminProxyTesterOptionsResponse)
def get_proxy_tester_options(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return proxy_tester_service.get_options(db)


@router.post("/run", response_model=AdminProxyTesterResponse)
async def run_proxy_test(
    data: AdminProxyTesterRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return await proxy_tester_service.run_test(data, db)
