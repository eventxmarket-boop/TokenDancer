import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.order import Order, OrderItem
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.order import OrderRead, OrderListItem, OrderItemRead
from app.services.account_service import account_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class OrderService:
    def create_from_cart(
        self, user_id: int, payment_method: str | None, db: Session
    ) -> OrderRead:
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            raise ValueError("购物车不存在")

        items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        if not items:
            raise ValueError("购物车为空")

        # 校验商品：必须存在且已上架
        for it in items:
            product = db.query(Product).filter(Product.id == it.product_id).first()
            if not product:
                raise ValueError(f"商品 ID={it.product_id} 不存在，无法下单")
            if not product.is_active:
                raise ValueError(f"商品「{product.name}」已下架，无法下单")

        # 计算总价（Decimal）
        total_amount = sum(it.unit_price * it.quantity for it in items)

        # 生成订单号
        order_no = f"ORD-{uuid.uuid4().hex[:12].upper()}"

        order = Order(
            user_id=user_id,
            order_no=order_no,
            status="pending",
            total_amount=total_amount,
            coupon_code=cart.coupon_code,
            payment_method=payment_method,
        )
        db.add(order)
        db.flush()

        # 创建订单项（写入真实商品名快照）
        for it in items:
            product = db.query(Product).filter(Product.id == it.product_id).first()
            order_item = OrderItem(
                order_id=order.id,
                product_id=it.product_id,
                product_name=product.name,
                quantity=it.quantity,
                unit_price=it.unit_price,
                subtotal=it.unit_price * it.quantity,
            )
            db.add(order_item)

        # 清空购物车项，保留购物车本身
        for it in items:
            db.delete(it)
        if cart.coupon_code:
            cart.coupon_code = None

        db.commit()
        db.refresh(order)
        return self._order_read(order, db)

    def list_orders(self, user_id: int, db: Session) -> list[OrderListItem]:
        orders = (
            db.query(Order)
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .all()
        )
        return [OrderListItem.model_validate(o) for o in orders]

    def get_order(self, order_id: int, user_id: int, db: Session) -> OrderRead | None:
        order = (
            db.query(Order)
            .filter(Order.id == order_id, Order.user_id == user_id)
            .first()
        )
        if not order:
            return None
        return self._order_read(order, db)

    def _order_read(self, order: Order, db: Session) -> OrderRead:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        return OrderRead(
            id=order.id,
            order_no=order.order_no,
            status=order.status,
            total_amount=float(order.total_amount),
            payment_method=order.payment_method,
            coupon_code=order.coupon_code,
            items=[OrderItemRead.model_validate(it) for it in items],
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    # ---- Order fulfillment: called after payment succeeds ----
    def fulfill_order(self, order_id: int, db: Session) -> OrderRead:
        """
        订单完成后处理权益发放。
        1. 验证订单存在且为 pending 状态
        2. 避免重复 fulfill
        3. 根据每个订单项的商品类型分流发放权益：
           - balance_topup：充值余额，写 ledger
           - subscription：创建/更新订阅权益
           - token_pack：创建 token 配额记录
        4. 更新订单状态为 paid
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"订单 {order_id} 不存在")
        if order.status == "paid":
            logger.info(f"Order {order_id} already fulfilled, skipping")
            return self._order_read(order, db)
        if order.status != "pending":
            raise ValueError(f"订单状态不是 pending，当前：{order.status}，无法处理")

        from app.services.subscription_service import subscription_service
        balance_topup_total = Decimal("0")

        for item in order.items:
            product = item.product
            product_type = getattr(product, "product_type", "balance_topup") or "balance_topup"

            if product_type == "balance_topup":
                balance_topup_total += Decimal(str(item.subtotal or 0))

            elif product_type == "subscription":
                days = getattr(product, "subscription_days", 30) or 30
                subscription_service.create_subscription(
                    user_id=order.user_id,
                    plan_name=product.name,
                    days=days,
                    db=db,
                    product_id=product.id,
                    order_id=order.id,
                )
                logger.info(f"[subscription] order {order_id}: created '{product.name}' {days} days")

            elif product_type == "token_pack":
                quota = getattr(product, "token_quota", 0) or 0
                if quota > 0:
                    subscription_service.create_token_grant(
                        user_id=order.user_id,
                        quota=quota,
                        db=db,
                        product_id=product.id,
                        order_id=order.id,
                    )
                    logger.info(f"[token_pack] order {order_id}: +{quota} tokens for '{product.name}'")

            else:
                # 未知类型，默认走余额充值
                balance_topup_total += Decimal(str(item.subtotal or 0))

        if balance_topup_total > 0:
            account_service.credit_balance(
                user_id=order.user_id,
                amount=balance_topup_total,
                db=db,
                order_id=order.id,
                operation="order_credit",
                remark=f"订单支付成功：{order.order_no}",
            )
            logger.info(f"[balance_topup] order {order_id}: +{balance_topup_total}")

        # 更新订单状态
        order.status = "paid"
        db.commit()
        db.refresh(order)
        return self._order_read(order, db)

    def cancel_order(self, order_id: int, user_id: int, db: Session) -> OrderRead:
        """
        取消订单（仅允许 pending 状态）。
        """
        order = db.query(Order).filter(
            Order.id == order_id, Order.user_id == user_id
        ).first()
        if not order:
            raise ValueError("订单不存在")
        if order.status != "pending":
            raise ValueError(f"订单状态为 {order.status}，无法取消")
        order.status = "cancelled"
        db.commit()
        db.refresh(order)
        return self._order_read(order, db)


order_service = OrderService()
