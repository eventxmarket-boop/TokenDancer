from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services.chat_service import chat_with_persona
from app.services.zhangxuefeng_research import (
    classify_zhangxuefeng_question,
    build_facts_summary,
    build_search_queries,
    rank_education_results,
    research_education_question,
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


class ZhangXuefengResearchTests(unittest.TestCase):
    def test_question_classifier_distinguishes_fact_framework_and_hybrid(self):
        self.assertEqual(classify_zhangxuefeng_question("人工智能专业值不值"), "hybrid")
        self.assertEqual(classify_zhangxuefeng_question("普通家庭怎么选方向"), "framework_only")
        self.assertEqual(classify_zhangxuefeng_question("某大学的保研率和就业率怎么样"), "fact_required")

    def test_research_fallback_returns_checklist_without_research_mode(self):
        with patch.dict("os.environ", {"ZHANGXUEFENG_RESEARCH_MODE": "stub"}):
            result = asyncio.run(research_education_question("人工智能专业值不值"))
        self.assertTrue(result["needs_research"])
        self.assertEqual(result["facts_summary"], [])
        self.assertTrue(result["sources_hint"])

    def test_build_search_queries_prefers_education_sources(self):
        queries = build_search_queries("陕西理科400分能报什么", "fact_required")
        self.assertEqual(len(queries), 3)
        self.assertTrue(any("site:gov.cn" in query or "site:edu.cn" in query for query in queries))
        self.assertTrue(any("录取分数线" in query or "院校名单" in query for query in queries))

    def test_rank_education_results_prioritizes_official_sources(self):
        ranked = rank_education_results(
            [
                {"title": "普通资讯", "snippet": "没有官方信息", "url": "https://news.example.com/a"},
                {"title": "学校招生简章", "snippet": "官方招生信息", "url": "https://zs.example.edu.cn"},
                {"title": "教育考试院公告", "snippet": "官方公告", "url": "https://www.sneea.cn/"},
            ]
        )
        self.assertEqual(ranked[0]["url"], "https://www.sneea.cn/")
        self.assertEqual(ranked[1]["url"], "https://zs.example.edu.cn")

    def test_build_facts_summary_is_empty_without_results(self):
        payload = build_facts_summary([], "人工智能专业值不值")
        self.assertEqual(payload["facts_summary"], [])
        self.assertTrue(payload["sources_hint"])

    def test_chat_service_calls_research_branch_for_fact_questions(self):
        temp_dir, db = _make_session()
        try:
            with patch("app.services.chat_service.research_education_question", new=AsyncMock()) as mock_research, patch(
                "app.services.chat_service.generate_reply", _fake_reply
            ):
                mock_research.return_value = {
                    "needs_research": True,
                    "question_class": "fact_required",
                    "facts_summary": ["需核实最新招生信息"],
                    "sources_hint": ["院校官网", "教育考试院"],
                    "search_query": "人工智能专业值不值",
                    "evidence": [],
                }
                result = asyncio.run(chat_with_persona("zhang_xue_feng", None, "人工智能专业值不值", db))

            self.assertTrue(result["reply"])
            mock_research.assert_awaited_once()
        finally:
            db.close()
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
