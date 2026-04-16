from __future__ import annotations

import unittest

from app.services.family_companion_service import (
    build_family_companion_context,
    retrieve_ranked_family_memories,
)


class FamilyCompanionServiceTests(unittest.TestCase):
    def test_family_companion_context_includes_emotion_rules(self):
        persona = {
            "persona_profile": {
                "relationship_type": "妈妈",
                "name": "妈妈",
                "tone": "温和、亲近",
                "catchphrases": ["先别急", "慢慢来"],
                "comfort_style": "先接住情绪，再慢慢安慰",
                "celebration_style": "先替你高兴，再顺着说",
                "boundaries": "不越界替你做决定",
            },
            "memory_base": {
                "shared_events": ["小时候一起吃饭", "夜里陪你写作业"],
                "important_advice": ["先照顾好自己", "遇事先稳住"],
                "daily_habits": ["会问你吃饭没", "会提醒你休息"],
                "emotional_triggers": ["考试压力", "工作烦心"],
                "chat_history_summary": "总是提醒你按时吃饭和休息",
                "memory_fragments": ["小时候一起写作业", "晚上陪你散步"],
                "text_materials": ["家书片段", "日常聊天摘录"],
            },
            "emotion_rules": {
                "summary": "先判断情绪，再提取记忆，再给温和回应",
                "emotion_state_priority": [
                    "难过 / 失落",
                    "焦虑 / 压力",
                    "开心 / 分享喜悦",
                ],
                "response_sequence": ["先接住当前情绪", "再调用熟悉记忆", "再给温和回应"],
                "response_temperature_map": {
                    "焦虑 / 压力": "安抚但不空泛，先帮对方稳住",
                },
                "memory_priority_rules": ["优先常说的话", "优先共同经历"],
                "boundary_rules": ["不伪造不确定的家庭事实"],
            },
        }

        context = build_family_companion_context(
            persona,
            [{"role": "user", "content": "我今天压力有点大"}],
            "我今天压力有点大",
        )

        self.assertIn("情绪规则摘要", context)
        self.assertIn("先判断情绪，再提取记忆，再给温和回应", context)
        self.assertIn("安抚但不空泛，先帮对方稳住", context)
        self.assertIn("先接住当前情绪", context)

    def test_family_companion_context_varies_by_subtype(self):
        base_persona = {
            "persona_profile": {
                "relationship_type": "家人陪伴",
                "name": "家人陪伴",
                "tone": "温和、亲近",
                "catchphrases": ["先别急", "慢慢来"],
                "comfort_style": "先接住情绪，再慢慢安慰",
                "celebration_style": "先替你高兴，再顺着说",
                "boundaries": "不越界替你做决定",
            },
            "memory_base": {
                "shared_events": ["家庭一起经历的重要时刻", "成长过程里的大事"],
                "important_advice": ["先看现实条件", "先把家庭安排稳住"],
                "daily_habits": ["会提醒你注意整体安排", "会关心你的成长进度"],
                "emotional_triggers": ["家庭压力", "成长选择", "重要决定"],
                "chat_history_summary": "把父母整体关心、提醒和建议先整理出来。",
                "memory_fragments": ["小时候一起写作业", "晚上陪你散步"],
                "text_materials": ["家书片段", "日常聊天摘录"],
            },
            "emotion_rules": {
                "summary": "先判断情绪，再提取记忆，再给温和回应",
                "emotion_state_priority": [
                    "难过 / 失落",
                    "焦虑 / 压力",
                    "开心 / 分享喜悦",
                ],
                "response_sequence": ["先接住当前情绪", "再调用熟悉记忆", "再给温和回应"],
                "response_temperature_map": {
                    "焦虑 / 压力": "安抚但不空泛，先帮对方稳住",
                },
                "memory_priority_rules": ["优先常说的话", "优先共同经历"],
                "boundary_rules": ["不伪造不确定的家庭事实"],
            },
        }

        mother_context = build_family_companion_context(
            {**base_persona, "family_subtype": "mother"},
            [{"role": "user", "content": "我今天压力有点大"}],
            "我今天压力有点大",
        )
        parents_context = build_family_companion_context(
            {**base_persona, "family_subtype": "parents"},
            [{"role": "user", "content": "我今天压力有点大"}],
            "我今天压力有点大",
        )
        other_context = build_family_companion_context(
            {**base_persona, "family_subtype": "other_family"},
            [{"role": "user", "content": "我今天压力有点大"}],
            "我今天压力有点大",
        )

        self.assertIn("家人子类型：妈妈", mother_context)
        self.assertIn("子类型重点：更偏接住情绪、细节照顾和熟悉安慰", mother_context)
        self.assertIn("家人子类型：父母", parents_context)
        self.assertIn("子类型重点：更偏家庭整体视角、稳定建议和共同记忆", parents_context)
        self.assertIn("家人子类型：其他家人", other_context)
        self.assertIn("子类型重点：更偏通用家庭陪伴和自然关心", other_context)
        self.assertNotEqual(mother_context, parents_context)
        self.assertNotEqual(mother_context, other_context)
        self.assertNotEqual(parents_context, other_context)

    def test_family_companion_ranked_memories_prefer_layer_by_emotion_and_topic(self):
        memory_base = {
            "episodic_memories": [
                "小时候你考试前总陪你复习",
                "那次家里一起过年",
            ],
            "semantic_memories": [
                "总提醒你先稳住再决定",
                "家庭里一直觉得先照顾好自己很重要",
            ],
            "procedural_memories": [
                "先别急",
                "我在呢，慢慢来",
                "会提醒你按时吃饭",
            ],
            "shared_events": ["小时候你考试前总陪你复习", "那次家里一起过年"],
            "important_advice": ["总提醒你先稳住再决定"],
            "daily_habits": ["会提醒你按时吃饭"],
            "chat_history_summary": "你压力大时会先安慰你。",
        }

        sad_ranked = retrieve_ranked_family_memories(
            memory_base,
            "难过 / 失落",
            "我最近工作压力很大",
            family_subtype="mother",
        )
        topic_ranked = retrieve_ranked_family_memories(
            memory_base,
            "寻求建议",
            "我在考虑考试和工作怎么选",
            family_subtype="parents",
        )

        self.assertTrue(sad_ranked)
        self.assertTrue(topic_ranked)
        self.assertIn("先别急", sad_ranked[0] + "".join(sad_ranked))
        self.assertTrue(any("复习" in item or "过年" in item for item in topic_ranked))
