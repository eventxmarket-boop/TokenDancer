import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.order import Order
from app.schemas.payment import PaymentIntentResponse

logger = logging.getLogger(__name__)


class PaymentProvider(ABC):
    @abstractmethod
    def create_payment_intent(self, order_id: int, amount: float, currency: str, db: Session) -> PaymentIntentResponse:
        ...

    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        ...


class StripeProvider(PaymentProvider):
    def __init__(self):
        self.secret_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import stripe
                stripe.api_key = self.secret_key
                self._client = stripe
            except ImportError:
                logger.warning("stripe package not installed")
                self._client = None
        return self._client

    def create_payment_intent(self, order_id: int, amount: float, currency: str, db: Session) -> PaymentIntentResponse:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"订单 {order_id} 不存在")
        if not self.secret_key or not self.client:
            raise RuntimeError("Stripe 支付尚未完成配置")

        payment_id = f"pi_{uuid.uuid4().hex[:24]}"
        payment_url = None
        try:
            import stripe
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency.lower(),
                metadata={"order_id": order_id, "payment_id": payment_id},
                automatic_payment_methods={"enabled": True},
            )
            payment_id = intent.id
            payment_url = getattr(intent, "next_action", None)
            logger.info(f"Created Stripe PaymentIntent {payment_id} for order {order_id}")
        except Exception as exc:
            logger.error(f"Stripe PaymentIntent creation failed for order {order_id}: {exc}")
            raise RuntimeError("Stripe 支付下单失败，请检查配置或稍后重试") from exc

        order.payment_id = payment_id
        db.commit()

        return PaymentIntentResponse(
            payment_id=payment_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            status="pending",
            payment_url=payment_url,
            created_at=datetime.now(timezone.utc),
        )

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        if not self.webhook_secret:
            logger.error("Stripe webhook verification failed: webhook secret not configured")
            return False
        if not self.client:
            logger.error("Stripe webhook verification failed: stripe client unavailable")
            return False
        try:
            import stripe
            event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            return event is not None
        except Exception as exc:
            logger.error(f"Stripe webhook verification failed: {exc}")
            return False


class UnsupportedPaymentProvider(PaymentProvider):
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def create_payment_intent(self, order_id: int, amount: float, currency: str, db: Session) -> PaymentIntentResponse:
        raise RuntimeError(f"支付提供方 {self.provider_name} 未完成生产配置")

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        return False


def get_payment_provider() -> PaymentProvider:
    provider = (settings.PAYMENT_PROVIDER or "").strip().lower()
    if provider == "stripe":
        return StripeProvider()
    return UnsupportedPaymentProvider(provider or "unknown")


payment_provider: PaymentProvider = get_payment_provider()
