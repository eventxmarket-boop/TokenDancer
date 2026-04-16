from __future__ import annotations

import unittest

from app.services.reunion_persona_service import (
    build_reunion_persona_context,
    detect_reunion_emotional_state,
    retrieve_ranked_reunion_memories,
)


class ReunionPersonaServiceTests(unittest.TestCase):
    def setUp(self):
        self.memory_base = {
            "episodic_memories": [
                "那次我们在门口见面",
                "一起走过旧街道的时候",
            ],
            "semantic_memories": [
                "你一直记得 ta 很温柔",
                "ta 总提醒你先稳住再做决定",
            ],
            "procedural_memories": [
                "先慢慢来",
                "记得吃饭",
                "我在呢",
            ],
            "legacy_summary": [
                "旧照片里的那段回忆",
                "一起在雨里回家的路",
            ],
            "chat_history_summary": "最近总会想起以前的聊天",
            "diary_notes": ["日记里写过那次重逢"],
            "letter_notes": ["信里反复说过先别急"],
            "photo_notes": ["照片里的旧街道"],
            "voice_notes": ["语音里说过注意休息"],
            "memory_fragments": ["门口的那次见面", "那句熟悉的提醒"],
            "shared_memories": ["共同经历的雨天"],
        }
        self.retrieval_policy = {
            "mode": "渐进式回忆",
            "progressive_recall": True,
            "priority_rules": [
                "先看最近对话，再看共同经历",
                "遇到具体场景，优先召回 episodic 记忆",
            ],
            "fallback_rules": [
                "记忆不足时先稳住情绪",
                "不要一次塞太多回忆",
            ],
            "max_memory_items": 3,
            "emotion_weight": 0.35,
            "topic_weight": 0.35,
            "layer_weight": 0.2,
            "safety_weight": 0.1,
        }
        self.safety_guardrails = {
            "boundaries": ["不激进刺激", "不替现实关系下结论"],
            "emotional_protection": ["先接住情绪，再慢慢回忆", "避免高压追问"],
            "avoid_triggers": ["不要把空白补成确定事实"],
            "avoid_dependency_language": True,
            "avoid_claiming_certainty": True,
            "avoid_afterlife_claims": True,
            "de_escalate_distress": True,
        }
        self.persona = {
            "reunion_persona_profile": {
                "relationship_type": "重逢人格",
                "name": "重逢人格",
                "tone": "克制、温柔、保留记忆感",
                "remembrance_style": "先慢慢回忆，再一点点靠近",
                "comfort_style": "先稳住情绪，再带着记忆慢慢说",
                "boundaries": "不激进刺激，不替现实关系下结论",
            },
            "reunion_memory_base": self.memory_base,
            "reunion_memory_retrieval_policy": self.retrieval_policy,
            "reunion_safety_guardrails": self.safety_guardrails,
        }

    def test_detect_reunion_emotional_state_prefers_grief_for_missing_someone(self):
        state = detect_reunion_emotional_state(
            "我最近很想念以前，也有点难过",
            [{"role": "assistant", "content": "我们慢慢回忆"}],
        )

        self.assertEqual(state, "怀念 / 失落")

    def test_ranked_reunion_memories_are_progressive_and_layer_aware(self):
        memories = retrieve_ranked_reunion_memories(
            self.memory_base,
            "怀念 / 失落",
            "我最近很想念以前在门口见面的那次",
            self.retrieval_policy,
            [{"role": "assistant", "content": "先慢慢回忆"}],
        )

        self.assertTrue(memories)
        self.assertLessEqual(len(memories), 3)
        self.assertTrue(any("门口" in item or "旧街道" in item for item in memories))
        self.assertTrue(any("先慢慢来" in item or "注意休息" in item for item in memories))

    def test_build_reunion_persona_context_includes_guardrails_and_progressive_recall(self):
        context = build_reunion_persona_context(
            self.persona,
            [{"role": "assistant", "content": "我们先慢慢回忆"}],
            "我有点想念以前了",
        )

        self.assertIn("当前情绪状态：怀念 / 失落", context)
        self.assertIn("是否渐进式回忆：是", context)
        self.assertIn("召回上限：3", context)
        self.assertIn("护栏状态：", context)
        self.assertIn("不激进刺激", context)
        self.assertIn("可调用回忆：", context)


if __name__ == "__main__":
    unittest.main()
