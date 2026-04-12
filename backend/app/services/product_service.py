from sqlalchemy.orm import Session
from app.models.product import Product


class ProductService:
    def list_products(
        self,
        db: Session,
        category: str | None = None,
        is_active: bool = True,
    ) -> list[Product]:
        q = db.query(Product)
        if is_active is not None:
            q = q.filter(Product.is_active == is_active)
        if category:
            q = q.filter(Product.category == category)
        return q.order_by(Product.sort_order.asc(), Product.created_at.desc()).all()

    def get_product(self, product_id: int, db: Session) -> Product | None:
        return db.query(Product).filter(Product.id == product_id).first()

    def get_by_slug(self, slug: str, db: Session) -> Product | None:
        return db.query(Product).filter(Product.slug == slug).first()

    def list_featured(self, db: Session, limit: int = 4) -> list[Product]:
        return (
            db.query(Product)
            .filter(Product.is_active == True)
            .order_by(Product.sort_order.asc(), Product.created_at.desc())
            .limit(limit)
            .all()
        )


product_service = ProductService()
