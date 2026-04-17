from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from app.services.llm_gateway import LLMGatewayError


class ReplyAssistantTests(unittest.TestCase):
    def test_reply_assistant_runtime_returns_structured_fallback_response(self):
        payload = {
            "message": "今晚能把方案发我吗？",
            "target_person_type": "boss",
            "scene_type": "follow_up",
            "current_context": "前面已经提过一次了。",
            "target_goal": "更职业",
            "tone_hint": "简明、克制",
            "relationship_status": "工作沟通中",
            "conversation_context": "对方还没回。",
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
            side_effect=LLMGatewayError("mocked unavailable model"),
        ):
            with TestClient(app) as client:
                response = client.post("/persona-api/reply-assistant", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "reply_assistant")
        self.assertEqual(body["target_person_type"], "boss")
        self.assertEqual(body["scene_type"], "follow_up")
        self.assertEqual(body["scene_label"], "跟进未回复")
        self.assertTrue(body["understanding_result"]["meaning_guess"])
        self.assertTrue(body["understanding_result"]["risk_flags"])
        self.assertGreaterEqual(len(body["reply_candidates"]), 4)
        self.assertGreaterEqual(len(body["predicted_replies"]), 3)
        self.assertTrue(body["recommended_reply"])
        self.assertTrue(body["tone_profile"]["label"])
        self.assertIn("职业化", body["tone_profile"]["style_tags"])


if __name__ == "__main__":
    unittest.main()
