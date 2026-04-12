from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import CartRead, CartItemRead, CartItemCreate, CartItemUpdate


def _build_cart_item(item: CartItem, product: Product) -> CartItemRead:
    return CartItemRead(
        id=item.id,
        product_id=item.product_id,
        product_name=product.name,
        product_slug=product.slug,
        delivery_type=product.delivery_type,
        category=product.category,
        quantity=item.quantity,
        unit_price=float(item.unit_price),
        created_at=item.created_at,
    )


def _calc_cart(db: Session, cart: Cart) -> CartRead:
    items_q = (
        db.query(CartItem)
        .options(joinedload(CartItem.product))
        .filter(CartItem.cart_id == cart.id)
        .all()
    )
    total = Decimal("0")
    item_reads = []
    for it in items_q:
        product = db.query(Product).filter(Product.id == it.product_id).first()
        if product:
            line_total = it.unit_price * it.quantity
            total += line_total
            item_reads.append(_build_cart_item(it, product))

    return CartRead(
        id=cart.id,
        user_id=cart.user_id,
        coupon_code=cart.coupon_code,
        items=item_reads,
        subtotal=float(total.quantize(Decimal("0.0001"))),
        total_quantity=sum(it.quantity for it in items_q),
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


class CartService:
    def get_or_create_cart(self, user_id: int, db: Session) -> Cart:
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        return cart

    def get_cart(self, user_id: int, db: Session) -> CartRead | None:
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            return None
        return _calc_cart(db, cart)

    def add_item(self, user_id: int, data: CartItemCreate, db: Session) -> CartRead:
        if data.quantity <= 0:
            raise ValueError("数量必须大于0")
        product = db.query(Product).filter(Product.id == data.product_id).first()
        if not product:
            raise ValueError("商品不存在")
        if not product.is_active:
            raise ValueError("商品未上架")

        cart = self.get_or_create_cart(user_id, db)

        existing = (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart.id, CartItem.product_id == data.product_id)
            .first()
        )
        if existing:
            existing.quantity += data.quantity
            db.commit()
        else:
            item = CartItem(
                cart_id=cart.id,
                product_id=data.product_id,
                quantity=data.quantity,
                unit_price=product.price_cny,
            )
            db.add(item)
            db.commit()

        db.refresh(cart)
        return _calc_cart(db, cart)

    def update_item(
        self, user_id: int, item_id: int, data: CartItemUpdate, db: Session
    ) -> CartRead:
        cart = self.get_or_create_cart(user_id, db)
        item = (
            db.query(CartItem)
            .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
            .first()
        )
        if not item:
            raise ValueError("购物车项不存在")

        if data.quantity <= 0:
            db.delete(item)
        else:
            item.quantity = data.quantity
        db.commit()
        db.refresh(cart)
        return _calc_cart(db, cart)

    def delete_item(self, user_id: int, item_id: int, db: Session) -> CartRead:
        cart = self.get_or_create_cart(user_id, db)
        item = (
            db.query(CartItem)
            .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
            .first()
        )
        if not item:
            raise ValueError("购物车项不存在")
        db.delete(item)
        db.commit()
        db.refresh(cart)
        return _calc_cart(db, cart)

    def set_coupon(self, user_id: int, coupon_code: str, db: Session) -> CartRead:
        cart = self.get_or_create_cart(user_id, db)
        code = coupon_code.strip()
        cart.coupon_code = code if code else None
        db.commit()
        db.refresh(cart)
        return _calc_cart(db, cart)


cart_service = CartService()
