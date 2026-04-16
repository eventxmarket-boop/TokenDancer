from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.core.logging import get_logger

logger = get_logger(__name__)


SCHEMA_UPGRADES: dict[str, dict[str, str]] = {
    "api_keys": {
        "expires_at": "TIMESTAMP NULL",
        "allowed_models": "VARCHAR(500) NULL",
        "last_used_model": "VARCHAR(100) NULL",
    },
    "usage_records": {
        "public_model_name": "VARCHAR(100) NULL",
        "provider_id": "INTEGER NULL",
        "provider_key_id": "INTEGER NULL",
        "upstream_model_name": "VARCHAR(100) NULL",
        "request_status": "VARCHAR(20) DEFAULT 'success'",
        "cost_amount": "NUMERIC(10, 6) DEFAULT 0",
    },
    "proxy_request_logs": {
        "request_origin": "VARCHAR(30) DEFAULT 'proxy'",
        "request_tag": "VARCHAR(100) NULL",
        "provider_switch_count": "INTEGER DEFAULT 0",
        "key_switch_count": "INTEGER DEFAULT 0",
        "failure_chain_summary": "TEXT NULL",
    },
    "chat_sessions": {
        "user_id": "INTEGER NULL",
        "title": "VARCHAR(120) NULL",
        "summary_text": "TEXT NULL",
        "summary_updated_at": "TIMESTAMP NULL",
    },
    "created_personas": {
        "user_id": "INTEGER NULL",
    },
}


def upgrade_runtime_schema(engine: Engine) -> None:
    """
    轻量运行时升级：
    - 仅补充新增列，不改动已有数据
    - 兼容本地 SQLite 和线上 PostgreSQL 的基础 ALTER TABLE ADD COLUMN 用法
    """
    inspector = inspect(engine)

    with engine.begin() as conn:
        for table_name, columns in SCHEMA_UPGRADES.items():
            if not inspector.has_table(table_name):
                continue

            existing_columns = {
                column["name"]
                for column in inspect(conn).get_columns(table_name)
            }

            for column_name, ddl in columns.items():
                if column_name in existing_columns:
                    continue

                statement = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"
                conn.execute(text(statement))
                logger.info(f"[schema-upgrade] Added {table_name}.{column_name}")
