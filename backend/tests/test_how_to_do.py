from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from app.services.how_to_do_service import ALL_GUA_CATALOG, generate_how_to_do_runtime


class HowToDoTests(unittest.TestCase):
    def test_how_to_do_catalog_contains_all_sixty_four_hexagrams(self):
        with TestClient(app) as client:
            response = client.post("/persona-api/how-to-do", json={"section": "catalog", "use_ai": False})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["section"], "catalog")
        self.assertEqual(len(body["catalog"]), 64)
        self.assertEqual(len({item["number"] for item in body["catalog"]}), 64)
        self.assertEqual(len(ALL_GUA_CATALOG), 64)

    def test_how_to_do_reference_returns_reference_cards(self):
        with TestClient(app) as client:
            response = client.post("/persona-api/how-to-do", json={"section": "reference", "use_ai": False})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["section"], "reference")
        self.assertTrue(body["cards"])
        self.assertEqual(body["cards"][0]["label"], "方向")

    def test_how_to_do_cast_uses_llm_when_available(self):
        payload = {
            "section": "cast",
            "cast_mode": "coin",
            "question": "现在适合推进吗？",
            "cast_seed": "20260418",
            "use_ai": True,
        }

        with patch(
            "app.services.how_to_do_service.generate_reply",
            return_value={
                "content": "本卦显示先观察，再根据动爻判断要不要推进。",
                "model": "mock-model",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "latency_ms": 1,
            },
        ) as mocked_generate:
            result = asyncio.run(generate_how_to_do_runtime(payload, db=object()))

        self.assertEqual(result["section"], "cast")
        self.assertTrue(mocked_generate.called)
        self.assertEqual(result["model_used"], "mock-model")
        self.assertIn("本卦", result["summary"])
        self.assertTrue(result["ai_interpretation"])


if __name__ == "__main__":
    unittest.main()
