import logging
import sys
from app.core.config import settings


def setup_logging():
    """配置全局日志格式和级别。"""

    # 避免重复添加 handler
    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    if settings.DEBUG:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    root.addHandler(handler)
    root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # 第三方库降噪
    for noisy in ["uvicorn.access", "uvicorn.asgi", "sqlalchemy.engine"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger。"""
    return logging.getLogger(name)
