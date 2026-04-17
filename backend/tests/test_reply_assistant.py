from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.schemas.reply_corpus import ReplyCorpusUpsertRequest
from fastapi.testclient import TestClient

from main import app
from app.services.llm_gateway import LLMGatewayError
from app.services.reply_assistant_service import generate_reply_assistant_runtime
from app.services.reply_corpus_service import save_reply_corpus


class ReplyAssistantTests(unittest.TestCase):
    def test_reply_assistant_runtime_calls_model_and_returns_concise_answer(self):
        payload = {
            "message": "今晚能把方案发我吗？",
            "target_person_type": "boss",
            "scene_type": "follow_up",
            "current_context": "前面已经提过一次了。",
            "target_goal": "更职业",
            "relationship_status": "工作沟通中",
            "conversation_context": "对方还没回。",
            "rewrite_mode": "formal",
            "raw_materials": {
                "chat_history_text": "前面已经提过一次了，今晚能给我吗？",
                "reply_style_samples_text": "更简短一点\n更职业一点",
                "uploaded_text_documents": [
                    {"filename": "follow-up.txt", "content": "请尽快反馈方案。"},
                ],
            },
        }

        with patch(
            "app.services.reply_assistant_service.generate_reply",
            return_value={
                "content": (
                    '{"judgment":"对方是在催你确认进度，先把结论说清楚。",'
                    '"recommended_reply":"收到，我先按这个方向处理，今晚把进展整理后再同步你。",'
                    '"risk_note":"别写太长，也别一次性承诺太满。",'
                    '"likely_consequence":"这样回通常能稳住节奏，但对方可能继续追问细节。"}'
                ),
                "model": "mock-model",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "latency_ms": 1,
            },
        ) as mocked_generate:
            with TestClient(app) as client:
                response = client.post("/persona-api/reply-assistant", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "reply_assistant")
        self.assertTrue(mocked_generate.called)
        self.assertEqual(body["judgment"], "对方是在催你确认进度，先把结论说清楚。")
        self.assertEqual(body["recommended_reply"], "收到，我先按这个方向处理，今晚把进展整理后再同步你。")
        self.assertEqual(body["risk_note"], "别写太长，也别一次性承诺太满。")
        self.assertEqual(body["likely_consequence"], "这样回通常能稳住节奏，但对方可能继续追问细节。")
        self.assertNotIn("reply_candidates", body)
        self.assertNotIn("predicted_replies", body)
        self.assertNotIn("material_summary", body)

    def test_reply_assistant_runtime_surfaces_llm_gateway_errors(self):
        payload = {
            "message": "今晚能把方案发我吗？",
            "target_person_type": "boss",
            "scene_type": "follow_up",
            "current_context": "前面已经提过一次了。",
            "target_goal": "更职业",
            "relationship_status": "工作沟通中",
            "conversation_context": "对方还没回。",
        }

        with patch(
            "app.services.reply_assistant_service.generate_reply",
            side_effect=LLMGatewayError("当前模型服务不可用：未配置启用的大模型 API Key"),
        ):
            with TestClient(app) as client:
                response = client.post("/persona-api/reply-assistant", json=payload)

        self.assertEqual(response.status_code, 503)
        self.assertIn("reply_assistant 未能调用模型", response.json()["detail"])

    def test_reply_assistant_runtime_includes_matching_reply_corpus(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        with SessionLocal() as db:
            save_reply_corpus(
                db,
                ReplyCorpusUpsertRequest(
                    title="暧昧推进",
                    target_person_type="crush",
                    scene_type="push_forward",
                    content="先接住，再轻轻往前走一步。",
                    sort_order=10,
                    is_enabled=True,
                ),
            )

            payload = {
                "message": "你今晚有空吗？",
                "target_person_type": "crush",
                "scene_type": "push_forward",
                "current_context": "前面已经聊了一会儿。",
                "target_goal": "更自然推进",
                "conversation_context": "对方语气有点试探。",
            }

            with patch(
                "app.services.reply_assistant_service.generate_reply",
                return_value={
                    "content": (
                        '{"judgment":"对方在等你接球，语气里有一点试探。",'
                        '"recommended_reply":"有空，怎么了？你要是想聊，我现在在。",'
                        '"risk_note":"别一上来就把话说满，先留点余地。",'
                        '"likely_consequence":"这样回会继续把话题往前推，对方大概率会接着聊。"}'
                    ),
                    "model": "mock-model",
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "latency_ms": 1,
                },
            ) as mocked_generate:
                response = asyncio.run(generate_reply_assistant_runtime(payload, db=db))

        self.assertEqual(response["mode"], "reply_assistant")
        self.assertTrue(mocked_generate.called)
        user_prompt = mocked_generate.call_args.args[0][1]["content"]
        self.assertIn("先接住，再轻轻往前走一步", user_prompt)
        self.assertIn("暧昧推进", user_prompt)
        self.assertEqual(response["judgment"], "对方在等你接球，语气里有一点试探。")


if __name__ == "__main__":
    unittest.main()
