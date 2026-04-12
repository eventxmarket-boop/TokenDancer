from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import setup_logging, get_logger
from app.core.schema_upgrade import upgrade_runtime_schema
from app.routers import health, auth, products, cart, orders, redeem, keys, usage, dashboard
from app.routers.admin import router as admin_router
from app.routers.profile import router as profile_router
from app.routers.payments import router as payments_router
from app.routers.payment_config import router as payment_config_router
from app.routers.admin_payment_config import router as admin_payment_config_router
from app.routers.admin_providers import router as admin_providers_router
from app.routers.admin_provider_keys import router as admin_provider_keys_router
from app.routers.admin_model_routes import router as admin_model_routes_router
from app.routers.admin_route_policies import router as admin_route_policies_router
from app.routers.admin_proxy_logs import router as admin_proxy_logs_router
from app.routers.admin_proxy_monitor import router as admin_proxy_monitor_router
from app.routers.admin_proxy_tester import router as admin_proxy_tester_router
from app.routers.admin_payment_events import router as admin_payment_events_router
from app.routers.proxy import router as proxy_router
from app.routers.admin_products import router as admin_products_router
from app.routers.content import router as content_router
from app.routers.admin_content import router as admin_content_router
from app.routers.admin_finance import router as admin_finance_router
from app.routers.admin_audit import router as admin_audit_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.billing import router as billing_router
from app.models import User, Product, Cart, CartItem, Order, OrderItem, RedeemCode, RedeemLog, APIKey, UsageRecord, BalanceLedger  # noqa: F401
from app.models.subscription import Subscription  # noqa: F401
from app.models.token_grant import TokenGrant  # noqa: F401

# 初始化日志
setup_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]
    # 从环境变量扩展 CORS（逗号分隔）
    if settings.APP_ENV == "prod":
        extra = settings.EXTRA_CORS_ORIGINS or ""
        cors_origins.extend([o.strip() for o in extra.split(",") if o.strip()])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 全局异常处理器
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception on {request.method} {request.url}")
        return JSONResponse(
            status_code=500,
            content={"detail": "服务内部异常，请稍后重试"}
        )

    # Register routers
    app.include_router(content_router)
    app.include_router(admin_content_router)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(products.router)
    app.include_router(cart.router)
    app.include_router(orders.router)
    app.include_router(redeem.router)
    app.include_router(admin_router)
    app.include_router(profile_router)
    app.include_router(payments_router)
    app.include_router(payment_config_router)
    app.include_router(admin_payment_config_router)
    app.include_router(keys.router)
    app.include_router(admin_providers_router)
    app.include_router(admin_provider_keys_router)
    app.include_router(admin_model_routes_router)
    app.include_router(admin_route_policies_router)
    app.include_router(admin_proxy_logs_router)
    app.include_router(admin_proxy_monitor_router)
    app.include_router(admin_proxy_tester_router)
    app.include_router(admin_payment_events_router)
    app.include_router(admin_finance_router)
    app.include_router(admin_audit_router)
    app.include_router(proxy_router)
    app.include_router(admin_products_router)
    app.include_router(usage.router)
    app.include_router(dashboard.router)
    app.include_router(subscriptions_router)
    app.include_router(billing_router)

    @app.on_event("startup")
    def on_startup():
        logger.info(f"[{settings.APP_NAME}] Starting up in {settings.APP_ENV} mode")

        # ---- SECURITY: Enforce strong SECRET_KEY in production ----
        insecure_secrets = {
            "change_this_to_a_long_random_secret",
            "secret", "changeme", "password", "test",
        }
        is_prod = settings.APP_ENV == "prod"
        key = settings.SECRET_KEY.strip()
        key_too_short = len(key) < 32
        key_is_placeholder = key.lower() in insecure_secrets

        if is_prod and (key_too_short or key_is_placeholder):
            import sys
            logger.critical(
                f"SECURITY: APP_ENV=prod but SECRET_KEY is insecure "
                f"(length={len(key)}, is_placeholder={key_is_placeholder}). "
                f"Set a strong SECRET_KEY in .env to start the server."
            )
            sys.exit(1)
        elif key_is_placeholder or key_too_short:
            logger.warning(
                f"SECURITY WARNING: SECRET_KEY appears weak (length={len(key)}). "
                f"Generate one: python3 -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )

        # ---- SECURITY: Enforce webhook secret in production ----
        webhook_secret = (settings.PAYMENT_WEBHOOK_SECRET or "").strip()
        stripe_webhook_secret = (settings.STRIPE_WEBHOOK_SECRET or "").strip()
        if is_prod and not (webhook_secret or stripe_webhook_secret):
            import sys
            logger.critical(
                "SECURITY: APP_ENV=prod but PAYMENT_WEBHOOK_SECRET/STRIPE_WEBHOOK_SECRET is empty. "
                "Webhook verification would be bypassed. Refusing to start."
            )
            sys.exit(1)

        Base.metadata.create_all(bind=engine)
        upgrade_runtime_schema(engine)
        logger.info(f"[{settings.APP_NAME}] Database ready")

    @app.on_event("shutdown")
    def on_shutdown():
        logger.info(f"[{settings.APP_NAME}] Shutting down")

    return app


app = create_app()
