from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.services.self_fill_assistant_service import generate_self_fill_assistant_reply


class SelfFillAssistantTests(unittest.TestCase):
    def test_self_fill_assistant_calls_model_and_keeps_scope(self):
        payload = {
            "message": "这个字段怎么填？",
            "create_mode": "light",
            "current_step": "3",
            "active_section": "自我主线",
            "active_field_key": "work_system_summary",
            "active_field_label": "材料说明",
            "field_context": "先写你最能代表自己的材料总览。",
            "conversation_context": "用户：这个字段怎么填？",
            "form_snapshot": {
                "name": "更完整的我",
                "work_system_summary": "先把素材池放进来。",
                "self_public_sources_text": "GitHub / 博客",
            },
        }

        with patch(
            "app.services.self_fill_assistant_service.generate_reply",
            new=AsyncMock(return_value={"content": "先把最能代表你的材料总览写出来，再补细节。"}),
        ) as mock_generate_reply:
            result = self.run_async(generate_self_fill_assistant_reply(payload, db=None))

        self.assertEqual(result["mode"], "self_fill_assistant")
        self.assertIn("材料总览", result["reply"])
        self.assertTrue(mock_generate_reply.await_count)
        system_prompt = mock_generate_reply.await_args.args[0][0]["content"]
        self.assertIn("只回答填写相关问题", system_prompt)
        self.assertIn("字段含义", system_prompt)

    def test_self_fill_assistant_empty_model_output_falls_back_to_refusal(self):
        payload = {
            "message": "这个字段怎么填？",
            "create_mode": "standard",
            "current_step": "3",
            "active_section": "自我主线",
            "active_field_key": "thinking_dna_points",
            "active_field_label": "自我判断要点",
            "form_snapshot": {},
        }

        with patch(
            "app.services.self_fill_assistant_service.generate_reply",
            new=AsyncMock(return_value={"content": ""}),
        ):
            result = self.run_async(generate_self_fill_assistant_reply(payload, db=None))

        self.assertEqual(result["mode"], "self_fill_assistant")
        self.assertIn("这一页", result["reply"])
        self.assertIn("标准模式", result["reply"])

    def test_self_fill_assistant_invalid_model_output_falls_back_to_page_guidance(self):
        payload = {
            "message": "这个字段怎么填？",
            "create_mode": "deep",
            "current_step": "3",
            "active_section": "自我知识源层",
            "active_field_key": "knowledge",
            "active_field_label": "自我知识源层",
            "form_snapshot": {},
        }

        with patch(
            "app.services.self_fill_assistant_service.generate_reply",
            new=AsyncMock(return_value={"content": "Not Found"}),
        ):
            result = self.run_async(generate_self_fill_assistant_reply(payload, db=None))

        self.assertEqual(result["mode"], "self_fill_assistant")
        self.assertIn("自我知识源层", result["reply"])
        self.assertNotIn("Not Found", result["reply"])
        self.assertNotIn("抱歉", result["reply"])

    @staticmethod
    def run_async(awaitable):
        import asyncio

        return asyncio.run(awaitable)


if __name__ == "__main__":
    unittest.main()
