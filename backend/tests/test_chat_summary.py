from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.schema_upgrade import upgrade_runtime_schema
from app.models.chat_session import ChatSession
from app.services.chat_service import chat_with_persona, get_chat_session_detail
from app.services.chat_summary_service import generate_session_summary, should_refresh_summary
from app.services.prompt_builder import build_chat_messages


class ChatSummaryTests(unittest.TestCase):
    def _make_session(self):
        temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(temp_dir.name) / "test.db"
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        upgrade_runtime_schema(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return temp_dir, SessionLocal()

    async def _fake_reply(self, messages, db=None):
        return {
            "content": "最终答案",
            "model": "gpt-admin-test",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            "latency_ms": 1,
        }

    def _seed_long_chat(self, db, turns: int = 11):
        session_id = None
        with patch("app.services.chat_service.generate_reply", self._fake_reply):
            for index in range(turns):
                result = asyncio.run(
                    chat_with_persona(
                        "zhang_xue_feng",
                        session_id,
                        f"第{index + 1}轮：陕西理科400分能报什么？",
                        db,
                    )
                )
                session_id = str(result["session_id"])
        return session_id

    def test_should_refresh_summary_after_threshold(self):
        self.assertFalse(should_refresh_summary(10))
        self.assertFalse(should_refresh_summary(20))
        self.assertTrue(should_refresh_summary(21, None, 1))
        self.assertTrue(should_refresh_summary(30, object(), 8))

    def test_generate_session_summary_compacts_history(self):
        summary = generate_session_summary(
            [
                {"role": "user", "content": "陕西理科400分，普通家庭，想学电力。"},
                {"role": "assistant", "content": "先看岗位和退路。"},
                {"role": "user", "content": "是否接受外省还没想好。"},
            ]
        )
        self.assertIn("当前讨论主题", summary)
        self.assertIn("已明确条件", summary)
        self.assertIn("待确认", summary)

    def test_summary_generated_after_long_history_and_hidden_from_detail(self):
        temp_dir, db = self._make_session()
        try:
            self._seed_long_chat(db, turns=11)
            session = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).first()
            self.assertIsNotNone(session)
            self.assertTrue((session.summary_text or "").strip())

            detail = get_chat_session_detail(db, session.session_id)
            self.assertIsNotNone(detail)
            self.assertNotIn("summary_text", detail)
            self.assertNotIn("summary_updated_at", detail)
            self.assertIn("messages", detail)
            self.assertGreater(len(detail["messages"]), 0)
        finally:
            db.close()
            temp_dir.cleanup()

    def test_prompt_builder_receives_session_summary(self):
        temp_dir, db = self._make_session()
        captured: dict[str, list[dict[str, str]]] = {}
        try:
            session_id = self._seed_long_chat(db, turns=11)
            with patch("app.services.chat_service.generate_reply") as mock_reply:
                mock_reply.return_value = {
                    "content": "最终答案",
                    "model": "gpt-admin-test",
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "latency_ms": 1,
                }

                def side_effect(messages, db=None):
                    captured["messages"] = messages
                    return mock_reply.return_value

                mock_reply.side_effect = side_effect
                asyncio.run(
                    chat_with_persona(
                        "zhang_xue_feng",
                        session_id,
                        "继续看电力和铁路哪个更稳？",
                        db,
                    )
                )

            messages = captured["messages"]
            self.assertGreaterEqual(len(messages), 2)
            self.assertIn("会话摘要", messages[0]["content"])
        finally:
            db.close()
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
