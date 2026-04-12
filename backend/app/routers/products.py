from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db
from app.schemas.product import ProductListItem, ProductRead
from app.services.product_service import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductListItem])
def list_products(
    category: str | None = None,
    db: Session = Depends(get_db),
):
    return product_service.list_products(db, category=category)


@router.get("/featured", response_model=list[ProductListItem])
def list_featured_products(
    limit: int = 4,
    db: Session = Depends(get_db),
):
    """
    返回精选商品（按 sort_order 升序取前 N 个 active 商品）。
    """
    return product_service.list_featured(db, limit=limit)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = product_service.get_product(product_id, db)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return product
