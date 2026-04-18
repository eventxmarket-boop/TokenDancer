from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from app.services.how_to_do_service import (
    ALL_GUA_CATALOG,
    _build_cast_result,
    _line_value_from_back_count,
    generate_how_to_do_runtime,
)


class HowToDoTests(unittest.TestCase):
    def test_three_coin_mapping_matches_traditional_line_values(self):
        self.assertEqual(_line_value_from_back_count(0), 6)
        self.assertEqual(_line_value_from_back_count(1), 7)
        self.assertEqual(_line_value_from_back_count(2), 8)
        self.assertEqual(_line_value_from_back_count(3), 9)

    def test_cast_relations_follow_hexagram_palace_rules(self):
        result = _build_cast_result(
            question="测试",
            category="朋友关系",
            cast_mode="manual",
            cast_seed="2026/04/18 07:30:00",
            manual_lines=[7, 8, 8, 8, 8, 8],
        )

        self.assertEqual(result["raw_result"]["hexagram_name"], "复")
        relations = [item["relation"] for item in result["raw_result"]["line_details"]]
        self.assertEqual(relations, ["妻财", "官鬼", "兄弟", "兄弟", "妻财", "子孙"])

    def test_transformed_hexagram_only_changes_moving_lines(self):
        result = _build_cast_result(
            question="测试",
            category="朋友关系",
            cast_mode="manual",
            cast_seed="2026/04/18 07:31:00",
            manual_lines=[6, 7, 8, 9, 7, 8],
        )

        raw_lines = result["raw_result"]["lines"]
        transformed = result["raw_result"]["transformed_line_details"]
        self.assertTrue(transformed)
        for index, line in enumerate(raw_lines):
            expected = ("阴" if line["yin_yang"] == "阳" else "阳") if line["value"] in {6, 9} else line["yin_yang"]
            self.assertEqual(transformed[index]["yin_yang"], expected)

    def test_cast_time_uses_input_seed_time(self):
        result = _build_cast_result(
            question="测试",
            category="朋友关系",
            cast_mode="manual",
            cast_seed="2026/04/18 07:20:56",
            manual_lines=[7, 7, 8, 8, 7, 8],
        )

        self.assertIn("2026年04月18日07:20:56", result["raw_result"]["day_label"])
        self.assertIn("壬辰时", result["raw_result"]["ganzhi_line"])

    def test_how_to_do_catalog_contains_all_sixty_four_hexagrams(self):
        with TestClient(app) as client:
            response = client.post("/persona-api/how-to-do", json={"section": "catalog", "use_ai": False})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["section"], "catalog")
        self.assertEqual(len(body["catalog"]), 64)
        self.assertEqual(len({item["number"] for item in body["catalog"]}), 64)
        self.assertEqual(len(ALL_GUA_CATALOG), 64)
        self.assertTrue(all(item.get("palace") for item in body["catalog"]))

    def test_how_to_do_sundial_returns_time_cards(self):
        with TestClient(app) as client:
            response = client.post("/persona-api/how-to-do", json={"section": "sundial", "use_ai": False})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["section"], "sundial")
        self.assertTrue(body["cards"])
        self.assertEqual(body["cards"][0]["label"], "当前时间")

    def test_how_to_do_cast_uses_llm_when_available(self):
        payload = {
            "section": "cast",
            "cast_mode": "coin",
            "question": "现在适合推进吗？",
            "category": "工作推进",
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
        self.assertIn("问念", {item["label"] for item in result["cards"]})

    def test_how_to_do_chat_uses_llm_when_available(self):
        payload = {
            "section": "chat",
            "user_message": "那我接下来该怎么做？",
            "cast_context": {
                "summary": "本卦显示先稳住节奏，再决定要不要推进。",
                "raw_result": {"hexagram_name": "复"},
            },
            "conversation_history": [
                {"role": "user", "content": "测这个项目能不能推进"},
                {"role": "assistant", "content": "先别急着推进，先看眼前条件。"},
            ],
            "use_ai": True,
        }

        with patch(
            "app.services.how_to_do_service.generate_reply",
            return_value={
                "content": "先把节奏稳住，再补一个最关键的信息点，确认后再推进会更顺。",
                "model": "mock-model",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "latency_ms": 1,
            },
        ) as mocked_generate:
            result = asyncio.run(generate_how_to_do_runtime(payload, db=object()))

        self.assertEqual(result["section"], "chat")
        self.assertTrue(mocked_generate.called)
        self.assertEqual(result["model_used"], "mock-model")
        self.assertIn("先把节奏稳住", result["ai_interpretation"])


if __name__ == "__main__":
    unittest.main()
