from __future__ import annotations

import unittest

from app.services.family_companion_service import build_family_companion_context


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

