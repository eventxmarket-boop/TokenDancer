from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models.user import User
from app.models.content_announcement import ContentAnnouncement
from app.models.content_page import ContentPage
from app.models.content_qr import ContentQr
from app.schemas.content import (
    AnnouncementCreate, AnnouncementUpdate, AnnouncementRead,
    PageUpdate, PageRead,
    QrCreate, QrUpdate, QrRead,
)

router = APIRouter(prefix="/content", tags=["content"])

@router.get("/announcements", response_model=list[AnnouncementRead])
def public_list_announcements(db: Session = Depends(get_db)):
    """公开：获取最近3条启用公告"""
    return db.query(ContentAnnouncement).filter(
        ContentAnnouncement.is_active == True
    ).order_by(ContentAnnouncement.published_at.desc()).limit(3).all()

@router.get("/announcements/latest", response_model=list[AnnouncementRead])
def public_list_announcements_latest(db: Session = Depends(get_db)):
    return public_list_announcements(db)

@router.get("/privacy", response_model=PageRead)
def public_get_privacy(db: Session = Depends(get_db)):
    page = db.query(ContentPage).filter(ContentPage.slug == "privacy").first()
    if not page:
        return PageRead(id=0, slug="privacy", title="隐私政策", content="暂无内容", updated_at=datetime.utcnow(), created_at=datetime.utcnow())
    return page

@router.get("/terms", response_model=PageRead)
def public_get_terms(db: Session = Depends(get_db)):
    page = db.query(ContentPage).filter(ContentPage.slug == "terms").first()
    if not page:
        return PageRead(id=0, slug="terms", title="服务条款", content="暂无内容", updated_at=datetime.utcnow(), created_at=datetime.utcnow())
    return page

@router.get("/qrs/latest", response_model=list[QrRead])
def public_list_qrs_latest(db: Session = Depends(get_db)):
    """公开：获取最近3条启用的二维码内容"""
    return db.query(ContentQr).filter(
        ContentQr.is_active == True
    ).order_by(ContentQr.sort_order.desc(), ContentQr.created_at.desc()).limit(3).all()
