from sqlalchemy.orm import Session
from app.models.order import Order
from app.schemas.admin_order import AdminOrderUpdate
from app.schemas.order import OrderRead, OrderListItem


class AdminOrderService:
    def list_orders(self, db: Session) -> list[OrderListItem]:
        orders = db.query(Order).order_by(Order.created_at.desc()).all()
        results = []
        for o in orders:
            data = {
                "id": o.id, "order_no": o.order_no, "status": o.status,
                "total_amount": float(o.total_amount), "payment_method": o.payment_method,
                "user_email": o.user.email if o.user else None,
                "user_id": o.user.id if o.user else None,
                "created_at": o.created_at,
            }
            results.append(OrderListItem.model_construct(**data))
        return results

    def get_order(self, order_id: int, db: Session) -> OrderRead | None:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None
        items = order.items
        user_email = order.user.email if order.user else None
        user_id = order.user.id if order.user else None
        data = dict(
            id=order.id, order_no=order.order_no, status=order.status,
            total_amount=float(order.total_amount), payment_method=order.payment_method,
            coupon_code=order.coupon_code, user_email=user_email, user_id=user_id,
            items=[dict(
                id=it.id, product_id=it.product_id,
                product_name=it.product_name, quantity=it.quantity,
                unit_price=float(it.unit_price), subtotal=float(it.subtotal),
                created_at=it.created_at,
            ) for it in items],
            created_at=order.created_at, updated_at=order.updated_at,
        )
        return OrderRead.model_construct(**data)

    def update_order(self, order_id: int, data: AdminOrderUpdate, db: Session) -> OrderRead | None:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None
        if data.status is not None:
            order.status = data.status
        db.commit()
        db.refresh(order)
        return self.get_order(order.id, db)


admin_order_service = AdminOrderService()
