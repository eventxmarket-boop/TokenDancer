from __future__ import annotations

import unittest
from unittest.mock import patch

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
                "raw_materials": {
                    "chat_history_text": "我在聊天里会先确认目标。",
                    "memory_notes_text": "我写过的判断片段。",
                    "text_materials_text": "资料里的一段文字。",
                    "uploaded_text_documents": [
                        {"filename": "self-notes.txt", "content": "我做事喜欢先看边界"},
                    ],
                    "uploaded_image_documents": [
                        {
                            "filename": "self-screenshot.png",
                            "mime_type": "image/png",
                            "size": 1024,
                            "data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+3d8AAAAASUVORK5CYII=",
                        }
                    ],
                    "ocr_extracted_texts": [
                        {
                            "filename": "self-screenshot.png",
                            "mime_type": "image/png",
                            "size": 1024,
                            "ocr_text": "做决定前先看条件",
                            "ocr_status": "success",
                        }
                    ],
                    "image_notes_text": "自我截图说明",
                    "voice_notes_text": "自我语音说明",
                },
            },
        }

        with patch(
            "app.services.create_wizard_service.ocr_service.extract_texts_from_uploaded_images"
        ) as mock_ocr_extract:
            mock_ocr_extract.return_value = [
                {
                    "filename": "family-photo.jpg",
                    "mime_type": "image/jpeg",
                    "size": 2048,
                    "ocr_text": "截图里写着：先别急，慢慢来",
                    "ocr_status": "success",
                }
            ]
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
        self.assertEqual(body["draft"]["raw_materials"]["uploaded_image_documents"][0]["filename"], "self-screenshot.png")
        self.assertEqual(body["draft"]["raw_materials"]["ocr_extracted_texts"][0]["ocr_status"], "success")
        self.assertIn("做决定前先看条件", body["draft"]["self_persona_unified"]["memory_evidence"]["summary"])

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
                "raw_materials": {
                    "chat_history_text": "先看家庭现实条件",
                    "memory_notes_text": "父母会先问家庭安排",
                    "text_materials_text": "家庭说明文字",
                    "uploaded_text_documents": [
                        {"filename": "relationship-notes.txt", "content": "父母更重视整体安排"},
                    ],
                    "uploaded_image_documents": [
                        {
                            "filename": "relationship-shot.png",
                            "mime_type": "image/png",
                            "size": 1024,
                            "data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+3d8AAAAASUVORK5CYII=",
                        }
                    ],
                    "ocr_extracted_texts": [
                        {
                            "filename": "relationship-shot.png",
                            "mime_type": "image/png",
                            "size": 1024,
                            "ocr_text": "家庭安排要先稳住",
                            "ocr_status": "success",
                        }
                    ],
                    "image_notes_text": "关系截图说明",
                    "voice_notes_text": "关系语音说明",
                },
            },
        }

        with patch("app.services.create_wizard_service.ocr_service.extract_texts_from_uploaded_images") as mock_ocr_extract:
            mock_ocr_extract.return_value = [
                {
                    "filename": "relationship-shot.png",
                    "mime_type": "image/png",
                    "size": 1024,
                    "ocr_text": "家庭安排要先稳住",
                    "ocr_status": "success",
                }
            ]
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
        self.assertTrue(body["draft"]["raw_materials"]["uploaded_image_documents"])
        self.assertTrue(body["draft"]["raw_materials"]["ocr_extracted_texts"])
        self.assertIn("家庭安排要先稳住", body["draft"]["material_summary"])

    def test_create_wizard_draft_endpoint_builds_source_persona_draft(self):
        payload = {
            "create_type": "source_persona",
            "group": "source",
            "source_repo": "anyone-to-skill",
            "display_name": "资料人格",
            "input_mode": "documents",
            "schema_key": "source_anyone_from_sources",
            "form_data": {
                "target_name": "资料人格",
                "material_type": "PDF / 文档",
                "material_description": "整理一批可继续蒸馏的资料材料。",
                "focus_points": "希望提炼观点和表达方式",
                "excluded_content": "不需要隐私内容",
                "raw_materials": {
                    "chat_history_text": "资料里提到先看目标再看路径。",
                    "memory_notes_text": "资料材料的关键摘录。",
                    "text_materials_text": "这里有一段重要的资料文本。",
                    "uploaded_text_documents": [
                        {"filename": "source-notes.md", "content": "资料里先整理目标和路径"},
                    ],
                    "uploaded_image_documents": [
                        {
                            "filename": "source-shot.png",
                            "mime_type": "image/png",
                            "size": 1024,
                            "data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+3d8AAAAASUVORK5CYII=",
                        }
                    ],
                    "ocr_extracted_texts": [
                        {
                            "filename": "source-shot.png",
                            "mime_type": "image/png",
                            "size": 1024,
                            "ocr_text": "资料里写着先看目标",
                            "ocr_status": "success",
                        }
                    ],
                    "image_notes_text": "资料图片说明",
                    "voice_notes_text": "资料语音说明",
                },
            },
        }

        with patch("app.services.create_wizard_service.ocr_service.extract_texts_from_uploaded_images") as mock_ocr_extract:
            mock_ocr_extract.return_value = [
                {
                    "filename": "source-shot.png",
                    "mime_type": "image/png",
                    "size": 1024,
                    "ocr_text": "资料里写着先看目标",
                    "ocr_status": "success",
                }
            ]
            with TestClient(app) as client:
                response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["draft"]["meta"]["create_type"], "source_persona")
        self.assertEqual(body["draft"]["meta"]["group"], "source")
        self.assertEqual(body["draft"]["meta"]["source_repo"], "anyone-to-skill")
        self.assertEqual(body["draft"]["meta"]["display_name"], "资料人格")
        self.assertEqual(body["draft"]["meta"]["input_mode"], "documents")
        self.assertEqual(body["draft"]["meta"]["schema_key"], "source_anyone_from_sources")
        self.assertIn("资料人格", body["draft"]["profile"])
        self.assertTrue(body["draft"]["raw_materials"]["uploaded_image_documents"])
        self.assertTrue(body["draft"]["raw_materials"]["ocr_extracted_texts"])
        self.assertIn("资料里写着先看目标", body["draft"]["material_summary"])

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
                "guided_memory_answers": {
                    "most_common_topics": "常聊吃饭和休息",
                    "comfort_style": "先接住情绪，再慢慢安慰",
                    "most_characteristic_event": "小时候陪我写作业",
                    "repeated_phrases": "先别急\n慢慢来",
                    "care_habits": "会提醒我按时吃饭",
                    "most_common_reminders": "记得休息和照顾自己",
                },
                "raw_materials": {
                    "chat_history_text": "妈总是提醒我按时吃饭和休息",
                    "memory_notes_text": "小时候一起写作业\n晚上陪你散步",
                    "text_materials_text": "家书片段\n日常聊天摘录",
                    "uploaded_text_documents": [
                        {"filename": "family-notes.txt", "content": "回家吃饭，别太晚"},
                    ],
                    "uploaded_image_documents": [
                        {
                            "filename": "family-photo.jpg",
                            "mime_type": "image/jpeg",
                            "size": 2048,
                            "data_url": "data:image/jpeg;base64,ZmFrZQ==",
                        }
                    ],
                    "ocr_extracted_texts": [
                        {
                            "filename": "family-photo.jpg",
                            "mime_type": "image/jpeg",
                            "size": 2048,
                            "ocr_text": "截图里写着：先别急，慢慢来",
                            "ocr_status": "success",
                        }
                    ],
                    "image_notes_text": "老照片说明",
                    "photo_notes_text": "老照片说明",
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
        self.assertIn("小时候一起写作业", body["draft"]["raw_materials"]["memory_notes_text"])
        self.assertIn("晚上陪你散步", body["draft"]["raw_materials"]["memory_notes_text"])
        self.assertIn("家书片段", body["draft"]["raw_materials"]["text_materials_text"])
        self.assertIn("日常聊天摘录", body["draft"]["raw_materials"]["text_materials_text"])
        self.assertEqual(body["draft"]["raw_materials"]["image_notes_text"], "老照片说明")
        self.assertEqual(body["draft"]["raw_materials"]["voice_notes_text"], "语音提醒片段")
        self.assertEqual(body["draft"]["raw_materials"]["uploaded_text_documents"][0]["filename"], "family-notes.txt")
        self.assertEqual(body["draft"]["raw_materials"]["uploaded_image_documents"][0]["filename"], "family-photo.jpg")
        self.assertEqual(body["draft"]["raw_materials"]["uploaded_image_documents"][0]["mime_type"], "image/jpeg")
        self.assertIn(
            body["draft"]["raw_materials"]["uploaded_image_documents"][0]["ocr_status"],
            {"success", "failed"},
        )
        self.assertTrue(body["draft"]["raw_materials"]["ocr_extracted_texts"])
        self.assertIn("先别急", body["draft"]["raw_materials"]["ocr_extracted_texts"][0]["ocr_text"])
        self.assertIn(
            "小时候一起写作业",
            " ".join(body["draft"]["memory_base"]["memory_fragments"]),
        )
        self.assertIn("先别急", " ".join(body["draft"]["memory_base"]["procedural_memories"]))
        self.assertIn(
            "先照顾好自己",
            " ".join(body["draft"]["memory_base"]["important_advice"]),
        )
        self.assertTrue(body["draft"]["memory_base"]["episodic_memories"])
        self.assertTrue(body["draft"]["memory_base"]["semantic_memories"])
        self.assertTrue(body["draft"]["memory_base"]["procedural_memories"])
        self.assertEqual(body["draft"]["guided_memory_answers"]["most_common_topics"], "常聊吃饭和休息")
        self.assertTrue(body["draft"]["raw_materials"]["uploaded_text_documents"])
        self.assertEqual(body["draft"]["family_subtype"], "mother")
        self.assertEqual(body["draft"]["emotion_rules"]["subtype_label"], "妈妈")
        self.assertIn("更偏接住情绪", body["draft"]["emotion_rules"]["subtype_focus"])
        self.assertIn("家人陪伴", body["draft"]["profile"])
        self.assertIn("妈妈", body["draft"]["profile"])

    def test_create_wizard_draft_endpoint_builds_family_companion_parents_draft(self):
        payload = {
            "create_type": "family_companion",
            "group": "relationship_family",
            "source_repo": "parents-skills+MamaSkill",
            "display_name": "家人陪伴",
            "input_mode": "parents",
            "schema_key": "family_companion_parents",
            "form_data": {
                "family_subtype": "parents",
                "relationship_type": "父母",
                "persona_name": "父母",
                "speech_style": "更稳、更完整，带家庭整体视角。",
                "catchphrases": "先稳住\n我们一起想办法",
                "comfort_style": "先稳住情绪，再给更完整的家庭建议。",
                "celebration_style": "先一起高兴，再顺着把家里的安排和共识说完整。",
                "relation_boundaries": "更偏家庭整体关心，不替你做决定。",
                "shared_events": "家庭一起经历的重要时刻\n成长过程里的大事",
                "important_advice": "先看现实条件\n先把家庭安排稳住",
                "daily_habits": "会提醒你注意整体安排\n会关心你的成长进度",
                "emotional_triggers": "家庭压力\n成长选择\n重要决定",
                "chat_history_summary": "把父母整体关心、提醒和建议先整理出来。",
                "memory_fragments": "家庭共同记忆\n成长过程里的关键片段",
                "text_materials": "家庭说明\n家书材料",
                "image_notes": "家庭照片 / 截图说明",
                "voice_notes": "家庭语音提醒",
                "raw_materials": {
                    "chat_history_text": "父母总是提醒我先稳住再做决定",
                    "memory_notes_text": "家庭一起经历的重要时刻\n成长过程里的大事",
                    "text_materials_text": "家书材料\n家庭说明",
                    "uploaded_text_documents": [
                        {"filename": "parents-notes.txt", "content": "先把家庭安排稳住"},
                    ],
                    "image_notes_text": "家庭照片 / 截图说明",
                    "photo_notes_text": "家庭照片 / 截图说明",
                    "voice_notes_text": "家庭语音提醒",
                },
            },
        }

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["draft"]["family_subtype"], "parents")
        self.assertEqual(body["draft"]["emotion_rules"]["subtype_label"], "父母")
        self.assertIn("更偏家庭整体视角", body["draft"]["emotion_rules"]["subtype_focus"])
        self.assertIn("家庭一起经历的重要时刻", " ".join(body["draft"]["memory_base"]["shared_events"]))
        self.assertIn("先把家庭安排稳住", " ".join(body["draft"]["memory_base"]["important_advice"]))
        self.assertTrue(body["draft"]["memory_base"]["episodic_memories"])
        self.assertTrue(body["draft"]["memory_base"]["semantic_memories"])
        self.assertTrue(body["draft"]["memory_base"]["procedural_memories"])
        self.assertIn("父母", body["draft"]["profile"])

    def test_create_wizard_draft_endpoint_keeps_family_companion_when_ocr_fails(self):
        payload = {
            "create_type": "family_companion",
            "group": "relationship_family",
            "source_repo": "parents-skills+MamaSkill",
            "display_name": "家人陪伴",
            "input_mode": "mother",
            "schema_key": "family_companion_mother",
            "form_data": {
                "family_subtype": "mother",
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
                    "uploaded_text_documents": [],
                    "uploaded_image_documents": [
                        {
                            "filename": "family-photo.jpg",
                            "mime_type": "image/jpeg",
                            "size": 2048,
                            "data_url": "data:image/jpeg;base64,ZmFrZQ==",
                        }
                    ],
                    "image_notes_text": "老照片说明",
                    "photo_notes_text": "老照片说明",
                    "voice_notes_text": "语音提醒片段",
                },
            },
        }

        with patch("app.services.create_wizard_service.ocr_service.extract_texts_from_uploaded_images") as mock_ocr_extract:
            mock_ocr_extract.return_value = []
            with TestClient(app) as client:
                response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["draft"]["family_subtype"], "mother")
        self.assertEqual(body["draft"]["raw_materials"]["uploaded_image_documents"][0]["ocr_status"], "待识别")
        self.assertEqual(body["draft"]["raw_materials"]["ocr_extracted_texts"], [])
        self.assertTrue(body["draft"]["memory_base"]["episodic_memories"] or body["draft"]["memory_base"]["procedural_memories"])

    def test_create_wizard_draft_endpoint_builds_family_companion_other_family_draft(self):
        payload = {
            "create_type": "family_companion",
            "group": "relationship_family",
            "source_repo": "parents-skills+MamaSkill",
            "display_name": "家人陪伴",
            "input_mode": "other_family",
            "schema_key": "family_companion_other_family",
            "form_data": {
                "family_subtype": "other_family",
                "relationship_type": "其他家人",
                "persona_name": "其他家人",
                "speech_style": "温和、自然、通用家庭陪伴感。",
                "catchphrases": "慢慢说\n我在呢\n先别急",
                "comfort_style": "先接住情绪，再给自然的陪伴和提醒。",
                "celebration_style": "先替你高兴，再顺着把好消息说完整。",
                "relation_boundaries": "保持亲近感，也保留合适边界。",
                "shared_events": "一起经历过的小事\n家里常见的互动",
                "important_advice": "保持联系\n照顾好自己",
                "daily_habits": "会问候你近况\n会留意你的状态",
                "emotional_triggers": "日常压力\n家庭琐事\n需要陪伴",
                "chat_history_summary": "把其他家人的关心方式和日常互动先整理出来。",
                "memory_fragments": "小事里的关心\n常见互动片段",
                "text_materials": "家庭便条\n补充说明",
                "image_notes": "图片 / 截图说明",
                "voice_notes": "语音说明",
                "raw_materials": {
                    "chat_history_text": "他/她会常常问候我的近况",
                    "memory_notes_text": "小事里的关心\n常见互动片段",
                    "text_materials_text": "家庭便条\n补充说明",
                    "uploaded_text_documents": [
                        {"filename": "other-family-notes.txt", "content": "保持联系，照顾好自己"},
                    ],
                    "image_notes_text": "图片 / 截图说明",
                    "photo_notes_text": "图片 / 截图说明",
                    "voice_notes_text": "语音说明",
                },
            },
        }

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["draft"]["family_subtype"], "other_family")
        self.assertEqual(body["draft"]["emotion_rules"]["subtype_label"], "其他家人")
        self.assertIn("更偏通用家庭陪伴", body["draft"]["emotion_rules"]["subtype_focus"])
        self.assertIn("小事里的关心", " ".join(body["draft"]["memory_base"]["memory_fragments"]))
        self.assertIn("保持联系", " ".join(body["draft"]["memory_base"]["important_advice"]))
        self.assertTrue(body["draft"]["memory_base"]["episodic_memories"])
        self.assertTrue(body["draft"]["memory_base"]["semantic_memories"])
        self.assertTrue(body["draft"]["memory_base"]["procedural_memories"])
        self.assertIn("其他家人", body["draft"]["profile"])

    def test_create_wizard_draft_endpoint_builds_family_companion_guided_memory_only_draft(self):
        payload = {
            "create_type": "family_companion",
            "group": "relationship_family",
            "source_repo": "parents-skills+MamaSkill",
            "display_name": "家人陪伴",
            "input_mode": "mother",
            "schema_key": "family_companion_mother",
            "form_data": {
                "family_subtype": "mother",
                "relationship_type": "妈妈",
                "persona_name": "妈妈",
                "guided_memory_answers": {
                    "most_common_topics": "总会聊吃饭和休息",
                    "comfort_style": "先接住情绪，再慢慢安慰",
                    "most_characteristic_event": "总在我考试前陪我复习",
                    "repeated_phrases": "慢慢来\n别急",
                    "care_habits": "会记得我生病时的照顾方式",
                    "most_common_reminders": "按时吃饭和早点睡",
                },
            },
        }

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()["draft"]
        self.assertEqual(body["family_subtype"], "mother")
        self.assertEqual(body["guided_memory_answers"]["most_common_topics"], "总会聊吃饭和休息")
        self.assertTrue(body["memory_base"]["episodic_memories"])
        self.assertTrue(body["memory_base"]["semantic_memories"])
        self.assertTrue(body["memory_base"]["procedural_memories"])

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
                "reunion_guided_memory_answers": {
                    "recall_scenes": "路过旧街道时最容易想起",
                    "how_they_addressed_you": "总是用很熟悉的昵称叫你",
                    "repeated_phrases": "先慢慢来\n记得吃饭",
                    "most_characteristic_moment": "会安静地陪你走一段路",
                    "deepest_impression": "克制但很温柔",
                    "care_style": "先问近况，再慢慢安慰",
                    "typical_reminders": "注意休息\n别太累",
                    "most_important_shared_memory": "一起在门口见面的那次",
                },
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
                    "uploaded_image_documents": [
                        {
                            "filename": "reunion-shot.png",
                            "mime_type": "image/png",
                            "size": 1024,
                            "data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+3d8AAAAASUVORK5CYII=",
                        }
                    ],
                    "ocr_extracted_texts": [
                        {
                            "filename": "reunion-shot.png",
                            "mime_type": "image/png",
                            "size": 1024,
                            "ocr_text": "旧截图里的话：先慢慢回忆",
                            "ocr_status": "success",
                        }
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
        self.assertIn("reunion_guided_memory_answers", body["draft"])
        self.assertEqual(body["draft"]["reunion_guided_memory_answers"]["recall_scenes"], "路过旧街道时最容易想起")
        self.assertTrue(body["draft"]["reunion_memory_base"]["episodic_memories"])
        self.assertTrue(body["draft"]["reunion_memory_base"]["semantic_memories"])
        self.assertTrue(body["draft"]["reunion_memory_base"]["procedural_memories"])
        self.assertGreaterEqual(body["draft"]["reunion_memory_base"]["episodic_count"], 1)
        self.assertGreaterEqual(body["draft"]["reunion_memory_base"]["semantic_count"], 1)
        self.assertGreaterEqual(body["draft"]["reunion_memory_base"]["procedural_count"], 1)
        self.assertIn("raw_materials", body["draft"])
        self.assertTrue(body["draft"]["raw_materials"]["uploaded_text_documents"])
        self.assertTrue(body["draft"]["raw_materials"]["uploaded_image_documents"])
        self.assertTrue(body["draft"]["raw_materials"]["ocr_extracted_texts"])
        self.assertIn("recall_stage", body["draft"]["reunion_memory_retrieval_policy"])
        self.assertIn(body["draft"]["reunion_memory_retrieval_policy"]["recall_stage"], {"light", "medium", "deep"})
        self.assertIn("reunion_guided_memory_answers", body["draft"])
        self.assertTrue(
            any("路过旧街道" in item or "先慢慢来" in item for item in body["draft"]["reunion_memory_base"]["legacy_summary"])
        )
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
                    "uploaded_image_documents": [
                        {
                            "filename": "intimate-shot.png",
                            "mime_type": "image/png",
                            "size": 1024,
                            "data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+3d8AAAAASUVORK5CYII=",
                        }
                    ],
                    "ocr_extracted_texts": [
                        {
                            "filename": "intimate-shot.png",
                            "mime_type": "image/png",
                            "size": 1024,
                            "ocr_text": "截图里写着：最近在忙什么",
                            "ocr_status": "success",
                        }
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
        self.assertTrue(body["draft"]["raw_materials"]["uploaded_image_documents"])
        self.assertTrue(body["draft"]["raw_materials"]["ocr_extracted_texts"])
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
