from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.services.llm_gateway import LLMGatewayError
from app.services.how_to_do_service import generate_how_to_do_runtime
from main import app


class HowToDoTests(unittest.TestCase):
    def test_how_to_do_zhouyi_calls_model_and_returns_cards(self):
        payload = {
            "mode": "zhouyi",
            "question": "我该怎么做？",
            "cast_seed": "seed-zhouyi",
            "use_ai": True,
        }

        with patch(
            "app.services.how_to_do_service.generate_reply",
            return_value={
                "content": "先稳住当前节奏，别急着把动作做满。",
                "model": "mock-model",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "latency_ms": 1,
            },
        ) as mocked_generate:
            with TestClient(app) as client:
                response = client.post("/persona-api/how-to-do", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "zhouyi")
        self.assertTrue(mocked_generate.called)
        self.assertIn("卦名", [card["label"] for card in body["cards"]])
        self.assertEqual(body["ai_interpretation"], "先稳住当前节奏，别急着把动作做满。")
        self.assertEqual(body["model_used"], "mock-model")

    def test_how_to_do_bazi_falls_back_when_model_unavailable(self):
        payload = {
            "mode": "bazi",
            "question": "我该怎么做？",
            "birth_year": 1994,
            "birth_month": 8,
            "birth_day": 18,
            "birth_hour": 9,
            "gender": "male",
            "use_ai": True,
        }

        with patch(
            "app.services.how_to_do_service.generate_reply",
            side_effect=LLMGatewayError("当前模型服务不可用：未配置启用的大模型 API Key"),
        ):
            result = asyncio.run(generate_how_to_do_runtime(payload, db=None))

        self.assertEqual(result["mode"], "bazi")
        self.assertIn("四柱：", result["summary"])
        self.assertTrue(result["cards"])
        self.assertNotEqual(result["ai_interpretation"], "")

    def test_how_to_do_liuyao_manual_cast_returns_transformed_hexagram(self):
        payload = {
            "mode": "liuyao",
            "question": "这个项目要不要继续推进？",
            "cast_seed": "liuyao-seed",
            "liuyao_cast_mode": "manual",
            "liuyao_lines": [9, 8, 7, 6, 7, 8],
            "use_ai": True,
        }

        with patch(
            "app.services.how_to_do_service.generate_reply",
            return_value={
                "content": "当前局势已经出现变化，先看动爻再判断推进节奏。",
                "model": "mock-model",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "latency_ms": 1,
            },
        ) as mocked_generate:
            result = asyncio.run(generate_how_to_do_runtime(payload, db=object()))

        self.assertEqual(result["mode"], "liuyao")
        self.assertTrue(mocked_generate.called)
        self.assertIn("起卦方式", [card["label"] for card in result["cards"]])
        self.assertIn("变卦", [card["label"] for card in result["cards"]])
        self.assertIn("transformed_hexagram", result["raw_result"])
        self.assertTrue(result["raw_result"]["lines"])
        self.assertEqual(result["ai_interpretation"], "当前局势已经出现变化，先看动爻再判断推进节奏。")


if __name__ == "__main__":
    unittest.main()
