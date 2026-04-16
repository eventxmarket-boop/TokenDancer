from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from main import app


class CreateWizardTests(unittest.TestCase):
    def test_create_wizard_draft_endpoint_builds_self_unified_draft(self):
        payload = {
            "create_type": "self_unified",
            "group": "self",
            "source_repo": "self-skill+nuwa-skill+forge-skill+digital-life",
            "display_name": "我的人格",
            "create_mode": "deep",
            "input_mode": "manual_profile",
            "input_modes": ["manual_profile", "chat_history", "documents", "memory_notes"],
            "schema_key": "self_unified",
            "form_data": {
                "name": "我的人格",
                "create_mode": "deep",
                "input_modes": ["manual_profile", "chat_history", "documents", "memory_notes"],
                "work_system_summary": "把做事方式整理成可以继续使用的人格骨架。",
                "work_system_points": "先看目标\n再看路径\n再看边界",
                "reply_persona_summary": "把回复方式整理成更像自己的表达。",
                "reply_persona_points": "直接一点\n清楚一点\n保留边界",
                "thinking_dna_summary": "把判断路径和取舍逻辑整理出来。",
                "thinking_dna_points": "先问条件\n再看出路\n再算代价",
                "memory_evidence_summary": "把聊天片段、文字材料和生活痕迹整理进去。",
                "memory_evidence_points": "聊天记录\n文字片段\n文件材料",
                "reflection_rules_summary": "把容易失真和需要保留的边界先写清楚。",
                "reflection_rules_points": "不夸张\n不越界\n不替自己下定论",
            },
        }

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("draft", body)
        self.assertEqual(body["draft"]["meta"]["create_type"], "self_unified")
        self.assertEqual(body["draft"]["meta"]["name"], "我的人格")
        self.assertEqual(body["draft"]["meta"]["display_name"], "我的人格")
        self.assertEqual(body["draft"]["meta"]["group"], "self")
        self.assertEqual(body["draft"]["meta"]["source_repo"], "self-skill+nuwa-skill+forge-skill+digital-life")
        self.assertEqual(body["draft"]["meta"]["schema_key"], "self_unified")
        self.assertEqual(body["draft"]["meta"]["create_mode"], "deep")
        self.assertEqual(
            body["draft"]["meta"]["input_modes"],
            ["manual_profile", "chat_history", "documents", "memory_notes"],
        )
        self.assertIn("self_persona_unified", body["draft"])
        self.assertTrue(body["draft"]["self_persona_unified"]["work_system"]["summary"])
        self.assertTrue(body["draft"]["self_persona_unified"]["thinking_dna"]["points"])
        self.assertTrue(body["draft"]["profile"].strip())
        self.assertTrue(body["draft"]["mindset"].strip())
        self.assertTrue(body["draft"]["guardrails"].strip())

    def test_create_wizard_draft_endpoint_keeps_relationship_payload_alignment(self):
        payload = {
            "create_type": "relationship_persona",
            "group": "relationship_family",
            "source_repo": "parents-skills",
            "display_name": "父母",
            "input_mode": "parents",
            "schema_key": "relationship_family_parents",
            "form_data": {
                "relationship_type": "父母",
                "persona_name": "父母",
                "speech_style": "温和但有要求",
                "decision_logic": "先看家庭现实条件",
                "purpose": "帮助理解父母视角",
                "relation_boundaries": "不越界",
            },
        }

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["draft"]["meta"]["create_type"], "relationship_persona")
        self.assertEqual(body["draft"]["meta"]["group"], "relationship_family")
        self.assertEqual(body["draft"]["meta"]["source_repo"], "parents-skills")
        self.assertEqual(body["draft"]["meta"]["display_name"], "父母")
        self.assertEqual(body["draft"]["meta"]["input_mode"], "parents")
        self.assertEqual(body["draft"]["meta"]["schema_key"], "relationship_family_parents")
        self.assertIn("父母", body["draft"]["profile"])

    def test_create_wizard_draft_endpoint_builds_family_companion_draft(self):
        payload = {
            "create_type": "family_companion",
            "group": "relationship_family",
            "source_repo": "parents-skills+MamaSkill",
            "display_name": "家人陪伴",
            "input_mode": "mother",
            "schema_key": "family_companion_mother",
            "form_data": {
                "relationship_type": "妈妈",
                "persona_name": "妈妈",
                "speech_style": "温和、熟悉、有点唠叨",
                "catchphrases": "先别急\n慢慢来",
                "comfort_style": "先接住情绪，再慢慢安慰",
                "celebration_style": "先替你高兴，再顺着把好消息说完整",
                "relation_boundaries": "不越界替你做决定",
                "shared_events": "小时候一起吃饭\n夜里陪你写作业",
                "important_advice": "先照顾好自己\n遇事先稳住",
                "daily_habits": "会问你吃饭没\n会提醒你休息",
                "emotional_triggers": "考试压力\n工作烦心\n好消息分享",
                "chat_history_summary": "总是提醒你按时吃饭和休息",
                "memory_fragments": "小时候一起写作业\n晚上陪你散步",
                "text_materials": "家书片段\n日常聊天摘录",
                "image_notes": "老照片说明",
                "voice_notes": "语音提醒片段",
                "raw_materials": {
                    "chat_history_text": "妈总是提醒我按时吃饭和休息",
                    "memory_notes_text": "小时候一起写作业\n晚上陪你散步",
                    "text_materials_text": "家书片段\n日常聊天摘录",
                    "uploaded_text_documents": [
                        {"filename": "family-notes.txt", "content": "回家吃饭，别太晚"},
                    ],
                    "image_notes_text": "老照片说明",
                    "voice_notes_text": "语音提醒片段",
                },
            },
        }

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["draft"]["meta"]["create_type"], "family_companion")
        self.assertEqual(body["draft"]["meta"]["group"], "relationship_family")
        self.assertEqual(body["draft"]["meta"]["source_repo"], "parents-skills+MamaSkill")
        self.assertEqual(body["draft"]["meta"]["display_name"], "家人陪伴")
        self.assertEqual(body["draft"]["meta"]["input_mode"], "mother")
        self.assertEqual(body["draft"]["meta"]["schema_key"], "family_companion_mother")
        self.assertEqual(body["draft"]["relationship_type"], "妈妈")
        self.assertIsNotNone(body["draft"]["persona_profile"])
        self.assertIsNotNone(body["draft"]["memory_base"])
        self.assertIn("emotion_rules", body["draft"])
        self.assertTrue(body["draft"]["emotion_rules"]["summary"])
        self.assertTrue(body["draft"]["emotion_rules"]["response_sequence"])
        self.assertIn("raw_materials", body["draft"])
        self.assertEqual(body["draft"]["raw_materials"]["chat_history_text"], "妈总是提醒我按时吃饭和休息")
        self.assertIn(
            "小时候一起写作业",
            " ".join(body["draft"]["memory_base"]["memory_fragments"]),
        )
        self.assertIn(
            "先照顾好自己",
            " ".join(body["draft"]["memory_base"]["important_advice"]),
        )
        self.assertTrue(body["draft"]["raw_materials"]["uploaded_text_documents"])
        self.assertIn("家人陪伴", body["draft"]["profile"])
        self.assertIn("妈妈", body["draft"]["profile"])

    def test_create_wizard_draft_endpoint_builds_reunion_persona_draft(self):
        payload = {
            "create_type": "reunion_persona",
            "group": "relationship_family",
            "source_repo": "reunion-skill",
            "display_name": "重逢人格",
            "input_mode": "chat_history",
            "schema_key": "reunion_persona_chat_history",
            "form_data": {
                "relationship_type": "重逢人格",
                "persona_name": "重逢人格",
                "speech_style": "克制、温和、保留记忆感",
                "remembrance_style": "先慢慢回忆，再一点点靠近",
                "comfort_style": "先稳住情绪，再带着记忆慢慢说",
                "relation_boundaries": "不激进刺激，不替现实关系下结论",
                "chat_history_summary": "过去常提起的片段与时间线",
                "diary_notes": "那年夏天的日记摘录",
                "letter_notes": "一封旧信里的话",
                "memory_fragments": "记忆片段 A\n记忆片段 B",
                "shared_memories": "共同经历的一件事\n共同记得的一句话",
                "priority_rules": "优先当前情绪相关记忆\n优先最近对话",
                "fallback_rules": "记忆不足时先稳住情绪\n不编造细节",
                "safety_boundaries": "不做激进刺激\n不替现实关系下结论",
                "emotional_protection": "先接住情绪\n避免高压追问",
                "avoid_triggers": "不要把空白补成确定事实\n不要一次抛出过多强刺激回忆",
                "photo_notes": "照片里的关键场景说明",
                "voice_notes": "口述回忆片段",
                "raw_materials": {
                    "chat_history_text": "过去常提起的片段与时间线",
                    "diary_text": "那年夏天的日记摘录",
                    "letter_text": "一封旧信里的话",
                    "memory_notes_text": "记忆片段 A\n记忆片段 B",
                    "uploaded_text_documents": [
                        {"filename": "reunion-notes.md", "content": "那天我们在门口见过"},
                    ],
                    "photo_notes_text": "照片里的关键场景说明",
                    "voice_notes_text": "口述回忆片段",
                },
            },
        }

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["draft"]["meta"]["create_type"], "reunion_persona")
        self.assertEqual(body["draft"]["meta"]["group"], "relationship_family")
        self.assertEqual(body["draft"]["meta"]["source_repo"], "reunion-skill")
        self.assertEqual(body["draft"]["meta"]["display_name"], "重逢人格")
        self.assertEqual(body["draft"]["meta"]["input_mode"], "chat_history")
        self.assertEqual(body["draft"]["meta"]["schema_key"], "reunion_persona_chat_history")
        self.assertEqual(body["draft"]["relationship_type"], "重逢人格")
        self.assertIsNotNone(body["draft"]["reunion_persona_profile"])
        self.assertIsNotNone(body["draft"]["reunion_memory_base"])
        self.assertIsNotNone(body["draft"]["reunion_memory_retrieval_policy"])
        self.assertIsNotNone(body["draft"]["reunion_safety_guardrails"])
        self.assertIn("raw_materials", body["draft"])
        self.assertTrue(body["draft"]["raw_materials"]["uploaded_text_documents"])
        self.assertIn("重逢人格", body["draft"]["profile"])

    def test_create_wizard_draft_endpoint_builds_intimate_companion_draft(self):
        payload = {
            "create_type": "intimate_companion",
            "group": "relationship_intimate",
            "source_repo": "relationship-training-skill+xinyi",
            "display_name": "关系理解",
            "input_mode": "relationship_understanding",
            "schema_key": "intimate_companion_relationship_understanding",
            "form_data": {
                "relationship_type": "关系理解",
                "persona_name": "关系理解",
                "relationship_stage": "关系有点紧张，需要先看表达方式",
                "speech_style": "自然、贴近、带一点熟悉感",
                "response_temperature": "先接住情绪，再顺着回应",
                "catchphrases": "我在听\n先别急",
                "relation_boundaries": "不越界，不替对方下结论",
                "conversation_samples": "你今天怎么了？\n最近在忙什么？",
                "interaction_rules": "先回应情绪，再进入内容本身",
                "relationship_goals": "让沟通更顺畅\n让关系更稳定",
                "key_memories": "一起经历过的重要时刻\n常聊的话题",
                "raw_materials": {
                    "chat_history_text": "最近在忙什么\n今天怎么了",
                    "memory_notes_text": "一起经历过的重要时刻",
                    "text_materials_text": "补充的文本材料",
                    "uploaded_text_documents": [
                        {"filename": "notes.txt", "content": "这是上传的文本材料"}
                    ],
                    "image_notes_text": "截图里记录了提醒",
                    "voice_notes_text": "语音里提到最近很忙",
                    "conflict_text": "那次误会",
                    "draft_message_text": "你今天怎么了？",
                    "recent_context_text": "最近在忙什么？",
                    "reply_style_samples_text": "我在听\n先别急",
                    "relationship_status_text": "关系有点紧张",
                    "interaction_patterns_text": "先回应情绪，再进入内容本身",
                    "history_text": "一起经历过的重要时刻",
                    "expression_samples_text": "我在听\n先别急",
                },
            },
        }

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["draft"]["meta"]["create_type"], "intimate_companion")
        self.assertEqual(body["draft"]["meta"]["group"], "relationship_intimate")
        self.assertEqual(body["draft"]["meta"]["source_repo"], "relationship-training-skill+xinyi")
        self.assertEqual(body["draft"]["meta"]["display_name"], "关系理解")
        self.assertEqual(body["draft"]["meta"]["input_mode"], "relationship_understanding")
        self.assertEqual(body["draft"]["meta"]["schema_key"], "intimate_companion_relationship_understanding")
        self.assertEqual(body["draft"]["relationship_type"], "关系理解")
        self.assertIsNotNone(body["draft"]["relationship_profile"])
        self.assertIsNotNone(body["draft"]["intimate_memory_base"])
        self.assertIn("raw_materials", body["draft"])
        self.assertTrue(body["draft"]["raw_materials"]["uploaded_text_documents"])
        self.assertIsNotNone(body["draft"]["intimate_understanding"])
        self.assertIn("亲密关系", body["draft"]["profile"])
        self.assertIn("关系理解", body["draft"]["profile"])

    def test_create_wizard_draft_endpoint_rejects_unsupported_type(self):
        payload = {
            "create_type": "digital_twin",
            "input_mode": "documents",
            "form_data": {},
        }

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
