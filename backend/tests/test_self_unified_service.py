from __future__ import annotations

import unittest

from app.services.self_unified_service import build_self_unified_draft, route_self_question, build_self_unified_context


class SelfUnifiedServiceTests(unittest.TestCase):
    def test_build_self_unified_draft_creates_four_layers_and_validation(self):
        draft = build_self_unified_draft(
            {
                "name": "我",
                "create_mode": "deep",
                "input_modes": ["manual_profile", "documents", "memory_notes"],
                "work_system_summary": "先把最能代表判断方式的材料整理好。",
                "work_system_points": "真实聊天\n项目复盘\n决策记录",
                "reply_persona_summary": "先把位置说清楚。",
                "reply_persona_points": "我最在意什么\n我最坚持什么",
                "thinking_dna_summary": "先判断条件，再决定下一步。",
                "thinking_dna_points": "先问条件\n再看出路\n再算代价",
                "memory_evidence_summary": "把静态材料和动态来源放进来。",
                "memory_evidence_points": "笔记 / 文章 / 项目文档",
                "reflection_rules_summary": "不编造经历，不把动态事实说死。",
                "reflection_rules_points": "不编造经历\n不假装熟悉",
                "self_deep_dive_answers_text": "我会特别坚定。\n我会保留余地。\n错误判断是在条件不足时下结论。",
                "self_validation_samples_text": "要不要接 offer？\n要不要转方向？\n要不要先做 MVP？",
                "raw_materials": {
                    "chat_history_text": "先看目标再看路径。",
                    "uploaded_text_documents": [{"filename": "notes.md", "content": "我习惯先看边界"}],
                    "uploaded_image_documents": [{"filename": "shot.png", "mime_type": "image/png", "size": 12}],
                    "ocr_extracted_texts": [{"filename": "shot.png", "mime_type": "image/png", "size": 12, "ocr_text": "先别急"}],
                },
            }
        )

        self.assertIn("self_persona_unified", draft)
        unified = draft["self_persona_unified"]
        self.assertIn("self_identity", unified)
        self.assertIn("self_decision_rules", unified)
        self.assertIn("self_voice", unified)
        self.assertIn("self_knowledge_sources", unified)
        self.assertIn("self_boundary_rules", unified)
        self.assertIn("profile_analysis_report", unified)
        self.assertIn("profile_interview", unified)
        self.assertTrue(unified["profile_analysis_report"]["report_summary"])
        self.assertGreaterEqual(unified["profile_interview"]["question_count"], 10)
        self.assertGreaterEqual(len(unified["question_routing"]), 5)
        self.assertGreaterEqual(len(unified["deep_dive_questions"]), 8)
        self.assertGreaterEqual(len(unified["validation_samples"]), 1)
        self.assertTrue(unified["materials_summary"])
        self.assertTrue(draft["profile"])
        self.assertTrue(draft["mindset"])
        self.assertTrue(draft["guardrails"])
        self.assertIn("profile_analysis_report", draft)
        self.assertIn("profile_interview", draft)

    def test_route_self_question_uses_topic_weights(self):
        route = route_self_question("要不要接这个 offer，还是先保底？")
        self.assertEqual(route["topic"], "职业 / 求职 / 成长判断")
        self.assertIn("self_decision_rules", route["weights"])
        self.assertIn("self_identity", route["weights"])

    def test_build_self_unified_context_mentions_route_and_boundary(self):
        persona = build_self_unified_draft(
            {
                "name": "我",
                "work_system_summary": "先看目标。",
                "reply_persona_summary": "先说结论。",
                "thinking_dna_summary": "先看条件。",
                "memory_evidence_summary": "先看材料。",
                "reflection_rules_summary": "不编造经历。",
            }
        )
        context = build_self_unified_context(persona, [], "学什么技术更值？")
        self.assertIn("问题路由", context)
        self.assertIn("学习 / 技术 / 工具选择", context)
        self.assertIn("回答要求", context)
