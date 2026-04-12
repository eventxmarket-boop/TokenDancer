from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


db_url = settings.DATABASE_URL
is_sqlite = db_url.startswith("sqlite")

engine_kwargs = {
    "echo": settings.DEBUG,
}
if is_sqlite:
    # SQLite 单线程检查在本地开发中需关闭；其他数据库不支持该参数
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(db_url, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
