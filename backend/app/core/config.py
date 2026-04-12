from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Demo Platform Backend"
    APP_ENV: str = "dev"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./demo_platform.db"

    SECRET_KEY: str = "change_this_to_a_long_random_secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    EXTRA_CORS_ORIGINS: str = ""

    PAYMENT_PROVIDER: str = "stripe"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    PAYMENT_WEBHOOK_SECRET: str = ""

    ALIPAY_QR_URL: str = ""
    ALIPAY_DISPLAY_NAME: str = "支付宝扫码支付"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM_ADDRESS: str = ""

    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_LOGIN: int = 10
    RATE_LIMIT_REGISTER: int = 5
    RATE_LIMIT_REDEEM: int = 20
    RATE_LIMIT_WEBHOOK: int = 60
    RATE_LIMIT_PASSWORD: int = 5

    LOGIN_COOLDOWN_ENABLED: bool = True
    LOGIN_MAX_FAILURES: int = 5
    LOGIN_COOLDOWN_SECONDS: int = 300

    RATE_LIMIT_PROXY: int = 60
    RATE_LIMIT_ADMIN_MUTATION: int = 30

    PROXY_MODE: str = "open"


settings = Settings()
