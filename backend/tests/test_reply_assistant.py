from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


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


if __name__ == "__main__":
    unittest.main()
