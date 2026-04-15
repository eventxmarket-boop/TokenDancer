from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.schema_upgrade import upgrade_runtime_schema
from app.services.chat_service import (
    chat_with_persona,
    get_chat_session_detail,
    get_recent_chat_sessions,
)


def _make_session():
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    upgrade_runtime_schema(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return temp_dir, SessionLocal()


def _make_legacy_session():
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "legacy.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE chat_sessions (
                    session_id VARCHAR(36) PRIMARY KEY,
                    persona_slug VARCHAR(100) NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
    return temp_dir, engine


async def _fake_reply(messages, db=None):
    return {
        "content": "最终答案",
        "model": "gpt-admin-test",
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        "latency_ms": 1,
    }


class ChatSessionTitleTests(unittest.TestCase):
    def test_chat_session_generates_title_and_recent_sessions_include_it(self):
        temp_dir, db = _make_session()
        try:
            with patch("app.services.chat_service.generate_reply", _fake_reply):
                result = asyncio.run(
                    chat_with_persona(
                        "zhang_xue_feng",
                        None,
                        "资源有限时怎么做取舍？",
                        db,
                    )
                )

            self.assertEqual(result["title"], "资源有限时怎么做取舍")

            detail = get_chat_session_detail(db, result["session_id"])
            self.assertIsNotNone(detail)
            self.assertEqual(detail["title"], "资源有限时怎么做取舍")

            recent = get_recent_chat_sessions(db, limit=5)
            self.assertGreaterEqual(len(recent), 1)
            self.assertEqual(recent[0]["title"], "资源有限时怎么做取舍")
            self.assertEqual(recent[0]["persona_name"], "张雪峰")
        finally:
            db.close()
            temp_dir.cleanup()

    def test_runtime_schema_upgrade_adds_title_column_to_legacy_chat_session_table(self):
        temp_dir, engine = _make_legacy_session()
        try:
            upgrade_runtime_schema(engine)
            columns = {column["name"] for column in inspect(engine).get_columns("chat_sessions")}
            self.assertIn("title", columns)
        finally:
            engine.dispose()
            temp_dir.cleanup()
