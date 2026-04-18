from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from app.services.how_to_do_service import (
    ALL_GUA_CATALOG,
    _answer_needs_repair,
    _append_scope_nudge,
    _build_cast_result,
    _build_divination_grounding,
    _build_interpretation_protocol,
    _compact_history_for_prompt,
    _line_value_from_back_count,
    _should_append_scope_nudge,
    _should_append_followup_question,
    generate_how_to_do_runtime,
)


class HowToDoTests(unittest.TestCase):
    FRONTEND_CATEGORIES = [
        "出行平安",
        "能否出行",
        "何时出行",
        "行人归来",
        "求财",
        "求官",
        "求职",
        "工作推进",
        "升迁调动",
        "考试测验",
        "学业文书",
        "感情回应",
        "婚姻复合",
        "表白推进",
        "朋友关系",
        "家宅关系",
        "父母长辈",
        "子女教育",
        "健康疾病",
        "诉讼官非",
        "失物寻人",
        "合作合伙",
        "交易签约",
        "投资买卖",
        "开店经营",
        "搬家迁移",
        "出国远行",
        "生产怀孕",
        "借贷还款",
        "项目进度",
        "面试入职",
        "其他",
    ]

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

    def test_interpretation_protocol_switches_focus_for_short_trade(self):
        base_result = _build_cast_result(
            question="清明前一天戊申日对做空有没有助力",
            category="做空交易",
            cast_mode="manual",
            cast_seed="2026/04/04 08:00:00",
            manual_lines=[7, 8, 8, 9, 7, 8],
        )
        protocol = _build_interpretation_protocol(
            question="清明前一天戊申日对做空有没有助力",
            category="做空交易",
            grounding=_build_divination_grounding(base_result),
        )

        self.assertEqual(protocol["question_type"], "做空交易")
        self.assertTrue(any("上涨是利还是害" in item for item in protocol["question_focus"]))
        self.assertTrue(protocol["time_alignment"]["must_follow_cast_time"])
        self.assertIn("符号解析", protocol["framework_name"])
        self.assertIn("hexagram_native_layer", protocol["framework_layers"])
        self.assertIn("question_mapping_layer", protocol["framework_layers"])
        self.assertIn("symbol_parsing", protocol)
        self.assertIn("relation_modeling", protocol)
        self.assertIn("core_conflict_extraction", protocol)
        self.assertIn("time_evolution", protocol)
        self.assertIn("symbol_relation_state_layer", protocol["framework_layers"])
        self.assertIn("symbol_system", protocol)
        self.assertIn("state_evolution", protocol)
        self.assertIn("answer_skeleton", protocol)
        self.assertIn("closing_question_style", protocol["answer_skeleton"])

    def test_interpretation_protocol_adds_direction_contract_for_lost_item(self):
        base_result = _build_cast_result(
            question="找东西，在什么方位",
            category="失物寻人",
            cast_mode="manual",
            cast_seed="2026/04/18 05:43:12",
            manual_lines=[7, 7, 7, 8, 8, 9],
        )
        protocol = _build_interpretation_protocol(
            question="找东西，在什么方位",
            category="失物寻人",
            grounding=_build_divination_grounding(base_result),
        )

        self.assertEqual(protocol["question_type"], "失物方位")
        self.assertTrue(protocol["answer_contract"]["direction_first"])
        self.assertIn("direction_reference", protocol)
        self.assertIn("乾", protocol["direction_reference"]["bagua_direction_map"])

    def test_interpretation_protocol_marks_generic_question_low_coverage(self):
        base_result = _build_cast_result(
            question="这件事背后的现实约束到底是什么",
            category="其他",
            cast_mode="manual",
            cast_seed="2026/04/18 09:00:00",
            manual_lines=[7, 8, 7, 8, 7, 8],
        )
        protocol = _build_interpretation_protocol(
            question="这件事背后的现实约束到底是什么",
            category="其他",
            grounding=_build_divination_grounding(base_result),
        )

        self.assertEqual(protocol["question_type"], "通用问事")
        self.assertFalse(protocol["question_type_meta"]["matched"])
        self.assertEqual(protocol["question_type_meta"]["coverage"], "low")
        self.assertIn("重新建立判断标准", protocol["question_type_meta"]["instruction"])

    def test_frontend_categories_are_covered_except_other(self):
        for category in self.FRONTEND_CATEGORIES:
            base_result = _build_cast_result(
                question=f"测试{category}",
                category=category,
                cast_mode="manual",
                cast_seed="2026/04/18 09:10:00",
                manual_lines=[7, 8, 7, 8, 7, 8],
            )
            protocol = _build_interpretation_protocol(
                question=f"测试{category}",
                category=category,
                grounding=_build_divination_grounding(base_result),
            )
            if category == "其他":
                self.assertEqual(protocol["question_type"], "通用问事")
                self.assertEqual(protocol["question_type_meta"]["coverage"], "low")
            else:
                self.assertNotEqual(protocol["question_type"], "通用问事", msg=f"{category} 未命中专门类型")
                self.assertEqual(protocol["question_type_meta"]["coverage"], "high", msg=f"{category} 覆盖度不够")

    def test_compact_history_trims_assistant_repetition(self):
        history = [
            {"role": "user", "content": "是否搬家，是续住还是搬家"},
            {
                "role": "assistant",
                "content": "核心结论：更偏搬。\n\n关键互动分析：这里展开很多很多很多很多很多很多很多很多很多很多很多很多很多很多很多很多很多很多很多很多。",
            },
        ]

        compacted = _compact_history_for_prompt(history)

        self.assertEqual(compacted[0]["content"], "是否搬家，是续住还是搬家")
        self.assertIn("核心结论：更偏搬。", compacted[1]["content"])
        self.assertLessEqual(len(compacted[1]["content"]), 220)

    def test_followup_question_stops_after_third_assistant_reply(self):
        history = [
            {"role": "assistant", "content": "第一条"},
            {"role": "assistant", "content": "第二条"},
            {"role": "assistant", "content": "第三条"},
        ]
        self.assertFalse(_should_append_followup_question("继续", conversation_history=history, cast_context={}))

    def test_scope_nudge_stops_after_second_assistant_reply(self):
        history = [
            {"role": "assistant", "content": "第一条"},
            {"role": "assistant", "content": "第二条"},
        ]
        self.assertFalse(_should_append_scope_nudge("继续", conversation_history=history, cast_context={}))

    def test_scope_nudge_is_inserted_before_trailing_question(self):
        content = "核心结论：更偏能成。\n\n你更想继续看结果，还是想看时间？"
        updated = _append_scope_nudge(content, "如果你觉得这里还偏宽，可以继续补细节。")
        self.assertIn("如果你觉得这里还偏宽，可以继续补细节。", updated)
        self.assertTrue(updated.endswith("你更想继续看结果，还是想看时间？"))

    def test_exam_generic_answer_is_flagged_for_repair(self):
        base_result = _build_cast_result(
            question="这次高考能不能如愿500分以上",
            category="考试测验",
            cast_mode="manual",
            cast_seed="2026/04/18 12:14:00",
            manual_lines=[7, 9, 8, 8, 8, 7],
        )
        protocol = _build_interpretation_protocol(
            question="这次高考能不能如愿500分以上",
            category="考试测验",
            grounding=_build_divination_grounding(base_result),
        )
        invalid, reason = _answer_needs_repair(
            question="这次高考能不能如愿500分以上",
            protocol=protocol,
            answer=(
                "核心结论：这卦先看颐的主势，眼下不必先慌，先顺着局势判断进退。"
                "卦象拆解：事情不是完全没有路，只是节奏要拿稳。"
            ),
        )
        self.assertTrue(invalid)
        self.assertIn("空壳模板", reason)

    def test_how_to_do_cast_repairs_generic_exam_answer(self):
        payload = {
            "section": "cast",
            "cast_mode": "coin",
            "question": "这次高考能不能如愿500分以上",
            "category": "考试测验",
            "cast_seed": "2026/04/18 12:14:44",
            "use_ai": True,
        }

        mocked_replies = [
            {
                "content": (
                    "核心结论：这卦先看颐的主势，眼下不必先慌，先顺着局势判断进退。"
                    "卦象拆解：事情不是完全没有路，只是节奏要拿稳。"
                ),
                "model": "mock-model",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "latency_ms": 1,
                "finish_reason": "stop",
            },
            {
                "content": (
                    "核心结论：这次高考更偏有机会摸到500分，但不是轻松稳过，关键看临场发挥和最后这段提分。"
                    "关键互动分析：这卦要重点看父母爻、子孙爻和世位，说明分数不是空来，要靠后段补强。"
                    "时间推演：临考前这一段比发榜后更关键。实际意义：现在最该补的是最容易丢分的那一块。"
                ),
                "model": "mock-model",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "latency_ms": 1,
                "finish_reason": "stop",
            },
        ]

        with patch(
            "app.services.how_to_do_service.generate_reply",
            side_effect=mocked_replies,
        ) as mocked_generate, patch(
            "app.services.how_to_do_service.research_how_to_do_question",
            return_value={
                "needs_research": True,
                "research_kind": "adaptive_context",
                "adaptive_reason": "回答偏空，需要补考试语境。",
                "facts_summary": ["高考类问题要把分数目标、发挥状态和最后提分空间区分开看。"],
                "sources_hint": ["背景资料"],
                "search_queries": ["高考 分数 语境"],
                "evidence": [],
            },
        ):
            result = asyncio.run(generate_how_to_do_runtime(payload, db=object()))

        self.assertEqual(mocked_generate.call_count, 2)
        self.assertIn("500分", result["ai_interpretation"])
        self.assertIn("父母爻", result["ai_interpretation"])

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
        ) as mocked_generate, patch(
            "app.services.how_to_do_service.research_how_to_do_question",
            return_value={
                "needs_research": True,
                "research_kind": "calendar_time",
                "facts_summary": ["2026年4月4日是清明前一天。"],
                "sources_hint": ["万年历"],
                "search_queries": ["2026 清明 前一天 日期"],
                "evidence": [],
            },
        ):
            result = asyncio.run(generate_how_to_do_runtime(payload, db=object()))

        self.assertEqual(result["section"], "cast")
        self.assertTrue(mocked_generate.called)
        self.assertEqual(result["model_used"], "mock-model")
        self.assertIn("本卦", result["summary"])
        self.assertTrue(result["ai_interpretation"])
        self.assertIn("问念", {item["label"] for item in result["cards"]})
        self.assertIn("research", result["raw_result"])
        sent_messages = mocked_generate.call_args.args[0]
        self.assertIn("六爻解卦师", sent_messages[0]["content"])
        self.assertIn("先完成卦象本体层分析", sent_messages[0]["content"])
        self.assertIn("不要直接把卦等同于吉凶", sent_messages[0]["content"])
        self.assertIn("先按起卦时间对应的日辰、月令、节气来解", sent_messages[0]["content"])
        self.assertIn("符号层、关系层、状态层", sent_messages[0]["content"])
        self.assertIn("二选一、是非题", sent_messages[0]["content"])
        self.assertIn("最后必须自然追问一句", sent_messages[0]["content"])
        self.assertIn("interpretation_protocol", sent_messages[1]["content"])
        self.assertIn("research_context", sent_messages[1]["content"])

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
        ) as mocked_generate, patch(
            "app.services.how_to_do_service.research_how_to_do_question",
            return_value={
                "needs_research": True,
                "research_kind": "general",
                "facts_summary": ["联网层补充了当前问题相关的日期与背景信息。"],
                "sources_hint": ["官方资料"],
                "search_queries": ["项目 推进 日期"],
                "evidence": [],
            },
        ):
            result = asyncio.run(generate_how_to_do_runtime(payload, db=object()))

        self.assertEqual(result["section"], "chat")
        self.assertTrue(mocked_generate.called)
        self.assertEqual(result["model_used"], "mock-model")
        self.assertIn("先把节奏稳住", result["ai_interpretation"])
        self.assertIn("latest_research", result["raw_result"])
        sent_messages = mocked_generate.call_args.args[0]
        self.assertIn("只允许围绕当前这卦", sent_messages[0]["content"])
        self.assertIn("续断时也要先完成卦象本体层分析", sent_messages[0]["content"])
        self.assertIn("先按这一卦对应的起卦时间和盘面继续断", sent_messages[0]["content"])
        self.assertIn("符号层、关系层、状态层", sent_messages[0]["content"])
        self.assertIn("继续、展开、细说", sent_messages[0]["content"])
        self.assertIn("最后也要自然反问一句", sent_messages[0]["content"])
        self.assertIn("interpretation_protocol", sent_messages[1]["content"])
        self.assertIn("research_context", sent_messages[1]["content"])

    def test_how_to_do_cast_removes_markdown_markers_from_llm_output(self):
        payload = {
            "section": "cast",
            "cast_mode": "coin",
            "question": "这件事还有没有机会？",
            "category": "关系进展",
            "cast_seed": "20260418",
            "use_ai": True,
        }

        with patch(
            "app.services.how_to_do_service.generate_reply",
            return_value={
                "content": "**核心结论：**先稳住。\n\n# 卦象拆解\n眼下先别急。",
                "model": "mock-model",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "latency_ms": 1,
            },
        ):
            result = asyncio.run(generate_how_to_do_runtime(payload, db=object()))

        self.assertNotIn("**", result["ai_interpretation"])
        self.assertNotIn("#", result["ai_interpretation"])
        self.assertIn("核心结论：先稳住。", result["ai_interpretation"])

    def test_how_to_do_cast_continues_when_model_is_truncated(self):
        payload = {
            "section": "cast",
            "cast_mode": "coin",
            "question": "这件事该怎么定",
            "category": "工作推进",
            "cast_seed": "20260418",
            "use_ai": True,
        }

        mocked_replies = [
            {
                "content": "核心结论：先别急着定。关键互动分析：父母爻主流程，眼下卡在资料和节奏。时间推演：再看月令",
                "model": "mock-model",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "latency_ms": 1,
                "finish_reason": "length",
            },
            {
                "content": "实际意义：先把材料补齐再推进，会更稳。风险提醒：现在仓促拍板，后面容易返工。你更想继续看推进时机，还是想看卡点到底压在哪一环？",
                "model": "mock-model",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "latency_ms": 1,
                "finish_reason": "stop",
            },
        ]

        with patch(
            "app.services.how_to_do_service.generate_reply",
            side_effect=mocked_replies,
        ):
            result = asyncio.run(generate_how_to_do_runtime(payload, db=object()))

        self.assertIn("实际意义：先把材料补齐再推进，会更稳。", result["ai_interpretation"])
        self.assertIn("风险提醒：现在仓促拍板", result["ai_interpretation"])


if __name__ == "__main__":
    unittest.main()
