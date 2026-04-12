from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_admin
from app.models.user import User
from app.models.product import Product
from app.schemas.product import ProductListItem, ProductRead
from app.schemas.admin_product import AdminProductCreate, AdminProductUpdate

router = APIRouter(prefix="/admin/products", tags=["admin-products"])


@router.get("", response_model=list[ProductListItem])
def list_admin_products(
    category: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理后台：商品列表，支持分类/上下架/搜索筛选。"""
    q = db.query(Product)
    if category:
        q = q.filter(Product.category == category)
    if is_active is not None:
        q = q.filter(Product.is_active == is_active)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    q = q.order_by(Product.sort_order.asc(), Product.id.asc())
    return q.all()


@router.get("/{product_id}", response_model=ProductRead)
def get_admin_product(
    product_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理后台：商品详情。"""
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="商品不存在")
    return p


@router.post("", response_model=ProductRead)
def create_admin_product(
    data: AdminProductCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理后台：新增商品。"""
    existing = db.query(Product).filter(Product.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="slug 已存在")
    p = Product(
        name=data.name,
        slug=data.slug,
        category=data.category,
        description=data.description,
        tag=data.tag,
        price_cny=data.price_cny,
        price_usd_value=data.price_usd_value,
        stock=data.stock,
        delivery_type=data.delivery_type,
        is_active=data.is_active,
        sort_order=data.sort_order,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.patch("/{product_id}", response_model=ProductRead)
def update_admin_product(
    product_id: int,
    data: AdminProductUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理后台：更新商品。"""
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="商品不存在")
    if data.slug:
        conflict = db.query(Product).filter(Product.slug == data.slug, Product.id != product_id).first()
        if conflict:
            raise HTTPException(status_code=409, detail="slug 已存在")
    update_data = data.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(p, field, val)
    db.commit()
    db.refresh(p)
    return p
