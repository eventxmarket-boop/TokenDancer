from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from app.services.llm_config_service import ResolvedLLMConfig
from app.services.llm_gateway import generate_reply
from app.services.prompt_builder import PLATFORM_CONSTRAINT
from app.services.text_sanitizer import strip_think_blocks


class FakeResponse:
    status_code = 200
    text = '{"ok": true}'

    def json(self):
        return {
            "model": "gpt-admin-test",
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 8,
                "total_tokens": 20,
            },
            "choices": [
                {
                    "message": {
                        "content": "<think>internal</think>最终答案\n\n<reasoning>trace</reasoning>",
                    }
                }
            ],
        }


class FakeClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        return FakeResponse()


class ThinkSanitizerTests(unittest.TestCase):
    def test_strip_think_blocks_removes_thinking_sections(self):
        text = "<think>secret</think>最终答案<reasoning>trace</reasoning><analysis>debug</analysis>"
        self.assertEqual(strip_think_blocks(text), "最终答案")

    def test_platform_constraint_blocks_think_output(self):
        self.assertIn("不要输出 <think>", PLATFORM_CONSTRAINT)
        self.assertIn("不要输出思考过程", PLATFORM_CONSTRAINT)

    def test_generate_reply_returns_sanitized_content(self):
        resolved_config = ResolvedLLMConfig(
            provider="openai_compatible",
            base_url="https://example.com/v1",
            api_key="sk-test",
            model_name="gpt-admin-test",
            temperature=0.7,
            max_tokens=128,
            source="db",
            config_id=1,
        )

        async def run_test():
            with patch("app.services.llm_gateway.resolve_llm_config", return_value=resolved_config), patch(
                "app.services.llm_gateway.httpx.AsyncClient",
                FakeClient,
            ):
                reply = await generate_reply([{"role": "user", "content": "test"}])
                self.assertEqual(reply["content"], "最终答案")
                self.assertEqual(reply["model"], "gpt-admin-test")
                self.assertEqual(
                    reply["usage"],
                    {
                        "prompt_tokens": 12,
                        "completion_tokens": 8,
                        "total_tokens": 20,
                    },
                )
                self.assertIsInstance(reply["latency_ms"], int)

        asyncio.run(run_test())
