from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_admin
from app.models.user import User
from app.models.content_announcement import ContentAnnouncement
from app.models.content_page import ContentPage
from app.models.content_qr import ContentQr
from app.schemas.content import (
    AnnouncementCreate, AnnouncementUpdate, AnnouncementRead,
    PageUpdate, PageRead,
    QrCreate, QrUpdate, QrRead,
)

router = APIRouter(prefix="/admin", tags=["admin-content"])

# ---- Announcements ----

@router.get("/announcements", response_model=list[AnnouncementRead])
def admin_list_announcements(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    return db.query(ContentAnnouncement).order_by(ContentAnnouncement.published_at.desc()).all()

@router.post("/announcements", response_model=AnnouncementRead)
def admin_create_announcement(data: AnnouncementCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    ann = ContentAnnouncement(**data.model_dump())
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return ann

@router.patch("/announcements/{ann_id}", response_model=AnnouncementRead)
def admin_update_announcement(ann_id: int, data: AnnouncementUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    ann = db.query(ContentAnnouncement).filter(ContentAnnouncement.id == ann_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="公告不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(ann, k, v)
    db.commit()
    db.refresh(ann)
    return ann

@router.delete("/announcements/{ann_id}")
def admin_delete_announcement(ann_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    ann = db.query(ContentAnnouncement).filter(ContentAnnouncement.id == ann_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="公告不存在")
    db.delete(ann)
    db.commit()
    return {"ok": True}

# ---- Privacy Policy ----

@router.get("/content/privacy", response_model=PageRead)
def admin_get_privacy(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    page = db.query(ContentPage).filter(ContentPage.slug == "privacy").first()
    if not page:
        page = ContentPage(slug="privacy", title="隐私政策", content="")
        db.add(page)
        db.commit()
        db.refresh(page)
    return page

@router.put("/content/privacy", response_model=PageRead)
def admin_update_privacy(data: PageUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    page = db.query(ContentPage).filter(ContentPage.slug == "privacy").first()
    if not page:
        page = ContentPage(slug="privacy", title="隐私政策", content="")
        db.add(page)
    if data.title is not None:
        page.title = data.title
    if data.content is not None:
        page.content = data.content
    db.commit()
    db.refresh(page)
    return page

# ---- Terms ----

@router.get("/content/terms", response_model=PageRead)
def admin_get_terms(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    page = db.query(ContentPage).filter(ContentPage.slug == "terms").first()
    if not page:
        page = ContentPage(slug="terms", title="服务条款", content="")
        db.add(page)
        db.commit()
        db.refresh(page)
    return page

@router.put("/content/terms", response_model=PageRead)
def admin_update_terms(data: PageUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    page = db.query(ContentPage).filter(ContentPage.slug == "terms").first()
    if not page:
        page = ContentPage(slug="terms", title="服务条款", content="")
        db.add(page)
    if data.title is not None:
        page.title = data.title
    if data.content is not None:
        page.content = data.content
    db.commit()
    db.refresh(page)
    return page

# ---- QR Contents ----

@router.get("/qrs", response_model=list[QrRead])
def admin_list_qrs(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    return db.query(ContentQr).order_by(ContentQr.sort_order.desc(), ContentQr.created_at.desc()).all()

@router.post("/qrs", response_model=QrRead)
def admin_create_qr(data: QrCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    qr = ContentQr(**data.model_dump())
    db.add(qr)
    db.commit()
    db.refresh(qr)
    return qr

@router.patch("/qrs/{qr_id}", response_model=QrRead)
def admin_update_qr(qr_id: int, data: QrUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    qr = db.query(ContentQr).filter(ContentQr.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="二维码内容不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(qr, k, v)
    db.commit()
    db.refresh(qr)
    return qr

@router.delete("/qrs/{qr_id}")
def admin_delete_qr(qr_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    qr = db.query(ContentQr).filter(ContentQr.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="二维码内容不存在")
    db.delete(qr)
    db.commit()
    return {"ok": True}

# ---- Content Pages (about, docs_center, faq, help_center) ----

@router.get("/content/pages", response_model=list[PageRead])
def admin_list_pages(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    return db.query(ContentPage).filter(ContentPage.slug.in_(["about", "docs_center", "faq", "help_center"])).order_by(ContentPage.id).all()

@router.get("/content/pages/{slug}", response_model=PageRead)
def admin_get_page(slug: str, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    page = db.query(ContentPage).filter(ContentPage.slug == slug).first()
    if not page:
        # Auto-create if not exists
        title_map = {"about": "关于我们", "docs_center": "文档中心", "faq": "常见问题", "help_center": "帮助中心"}
        page = ContentPage(slug=slug, title=title_map.get(slug, slug), content="")
        db.add(page)
        db.commit()
        db.refresh(page)
    return page

@router.put("/content/pages/{slug}", response_model=PageRead)
def admin_update_page(slug: str, data: PageUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    page = db.query(ContentPage).filter(ContentPage.slug == slug).first()
    if not page:
        title_map = {"about": "关于我们", "docs_center": "文档中心", "faq": "常见问题", "help_center": "帮助中心"}
        page = ContentPage(slug=slug, title=title_map.get(slug, slug), content="")
        db.add(page)
    if data.title is not None:
        page.title = data.title
    if data.content is not None:
        page.content = data.content
    db.commit()
    db.refresh(page)
    return page
