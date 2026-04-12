from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardSummary)
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return dashboard_service.get_summary(current_user.id, db)
