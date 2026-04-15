from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services.chat_service import (
    chat_with_persona,
    clear_chat_session,
    get_chat_session_detail,
    get_latest_chat_session_for_persona,
)


def _make_session():
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return temp_dir, SessionLocal()


async def _fake_reply(messages, db=None):
    return {
        "content": "最终答案",
        "model": "gpt-admin-test",
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        "latency_ms": 1,
    }


class ChatSessionPersistenceTests(unittest.TestCase):
    def test_chat_session_restore_and_clear_creates_new_session(self):
        temp_dir, db = _make_session()
        try:
            with patch("app.services.chat_service.generate_reply", _fake_reply):
                first = asyncio.run(
                    chat_with_persona("zhang_xue_feng", None, "第一问", db)
                )
                second = asyncio.run(
                    chat_with_persona(
                        "zhang_xue_feng",
                        first["session_id"],
                        "第二问",
                        db,
                    )
                )

            self.assertEqual(first["session_id"], second["session_id"])

            detail = get_chat_session_detail(db, first["session_id"])
            self.assertIsNotNone(detail)
            self.assertEqual(detail["persona_slug"], "zhang_xue_feng")
            self.assertEqual(len(detail["messages"]), 4)
            self.assertEqual(detail["messages"][0]["content"], "第一问")
            self.assertEqual(detail["messages"][1]["content"], "最终答案")

            latest = get_latest_chat_session_for_persona(db, "zhang_xue_feng")
            self.assertIsNotNone(latest)
            self.assertEqual(latest["session_id"], first["session_id"])
            self.assertEqual(len(latest["messages"]), 4)

            new_session_id = clear_chat_session(db, first["session_id"])
            self.assertNotEqual(new_session_id, first["session_id"])

            old_detail = get_chat_session_detail(db, first["session_id"])
            self.assertIsNotNone(old_detail)
            self.assertEqual(len(old_detail["messages"]), 4)

            new_detail = get_chat_session_detail(db, new_session_id)
            self.assertIsNotNone(new_detail)
            self.assertEqual(new_detail["persona_slug"], "zhang_xue_feng")
            self.assertEqual(len(new_detail["messages"]), 0)

            latest_after_clear = get_latest_chat_session_for_persona(db, "zhang_xue_feng")
            self.assertIsNotNone(latest_after_clear)
            self.assertEqual(latest_after_clear["session_id"], new_session_id)
            self.assertEqual(len(latest_after_clear["messages"]), 0)
        finally:
            db.close()
            temp_dir.cleanup()
