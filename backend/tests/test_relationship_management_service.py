from __future__ import annotations

import unittest

from app.services.relationship_management_service import (
    build_relationship_management_context,
    infer_relationship_management_focus,
    select_relationship_management_memory_layers,
)


class RelationshipManagementServiceTests(unittest.TestCase):
    def test_infer_focus_prefers_understanding_for_analysis_language(self):
        focus = infer_relationship_management_focus(
            "想理解 ta 这句话什么意思，分析一下雷区和信号",
            "沟通训练",
            "表达意图判断",
        )

        self.assertEqual(focus["analysis_focus"], "understanding")
        self.assertGreater(float(focus["understanding_weight"]), float(focus["maintenance_weight"]))

    def test_infer_focus_prefers_maintenance_for_long_term_language(self):
        focus = infer_relationship_management_focus(
            "长期相处和关系经营",
            "想修复冷战并改善相处",
            "稳定陪伴与安抚",
        )

        self.assertEqual(focus["analysis_focus"], "maintenance")
        self.assertGreater(float(focus["maintenance_weight"]), float(focus["understanding_weight"]))

    def test_infer_focus_returns_balanced_for_mixed_language(self):
        focus = infer_relationship_management_focus(
            "理解 信号 雷区 沟通",
            "经营 长期 稳定 修复",
            "表达 关系",
        )

        self.assertEqual(focus["analysis_focus"], "balanced")
        self.assertAlmostEqual(
            float(focus["understanding_weight"]) + float(focus["maintenance_weight"]) + float(focus["message_push_weight"]),
            1.0,
            places=2,
        )

    def test_infer_focus_prefers_message_push_for_send_before_preview_language(self):
        focus = infer_relationship_management_focus(
            "这句要不要发，先帮我看看 TA 可能怎么回，先练一遍再发出去",
            "发送前预演关键节点",
            "暧昧推进和候选回复",
        )

        self.assertEqual(focus["analysis_focus"], "message_push")
        self.assertGreater(float(focus["message_push_weight"]), float(focus["understanding_weight"]))
        self.assertGreater(float(focus["message_push_weight"]), float(focus["maintenance_weight"]))

    def test_recall_stage_downshifts_when_emotional_state_is_heavy(self):
        memory_base = {
            "relationship_memory": ["共同经历：一起走过那次搬家"],
            "interaction_samples": ["互动：先回应情绪，再进入内容"],
            "style_samples": ["风格：先接住情绪"],
            "candidate_reply_cues": ["建议：慢一点，先稳住"],
        }

        selected = select_relationship_management_memory_layers(
            memory_base,
            "难过 / 失落",
            "我今天很难过，先别讲太多",
            history=[{"role": "user", "content": "我今天很难过"}],
        )

        self.assertEqual(selected["recall_stage"], "light")
        self.assertLessEqual(len(selected["selected_memories"]), 2)
        self.assertTrue(selected["selected_memories"])

    def test_recall_stage_prefers_message_push_cues_for_send_before_preview_context(self):
        memory_base = {
            "relationship_memory": ["共同经历：一起规划下一次见面"],
            "interaction_samples": ["互动：先听，再决定怎么回"],
            "style_samples": ["风格：语气克制，先预演"],
            "candidate_reply_cues": ["建议：先练一遍，再发出去"],
            "message_push_cues": ["这句要不要发", "先帮我看看 TA 可能怎么回"],
        }

        selected = select_relationship_management_memory_layers(
            memory_base,
            "期待 / 紧张",
            "这句要不要发，先帮我看看 TA 可能怎么回",
            history=[{"role": "user", "content": "这句要不要发"}],
        )

        self.assertEqual(selected["recall_stage"], "push")
        self.assertLessEqual(len(selected["selected_memories"]), 4)
        self.assertTrue(selected["message_push_cues"])

    def test_build_context_contains_focus_and_ranked_memories(self):
        persona = {
            "relationship_management_profile": {
                "relationship_type": "关系经营",
                "name": "关系经营",
                "relationship_stage": "稳定相处中",
                "tone": "自然、克制、熟悉",
                "response_temperature": "先接住，再慢慢说",
                "catchphrases": ["我在听", "先别急"],
                "boundaries": "不越界",
            },
            "relationship_management_memory_base": {
                "relationship_memory": ["共同经历：那次我们一起熬夜改方案"],
                "interaction_samples": ["互动样本：先回应情绪，再进入内容"],
                "style_samples": ["风格样本：语气柔和，先稳住再说"],
                "candidate_reply_cues": ["建议线索：先安抚，再推进下一步"],
                "message_push_cues": ["这句要不要发", "先练一遍再发出去"],
            },
        }

        context = build_relationship_management_context(
            persona,
            [{"role": "user", "content": "我们上次一起熬夜改方案时，你是怎么想的"}],
            "我们上次一起熬夜改方案时，你是怎么想的",
        )

        self.assertIn("亲密关系路径：关系经营", context)
        self.assertIn("分析重心：", context)
        self.assertIn("当前召回：", context)
        self.assertIn("共同经历：那次我们一起熬夜改方案", context)
        self.assertIn("消息推进线索：", context)


if __name__ == "__main__":
    unittest.main()
