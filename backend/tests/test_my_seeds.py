from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.created_persona import CreatedPersona
from app.models.user import User
from main import app


class MySeedsTests(unittest.TestCase):
    def _register_test_user(self, client: TestClient, prefix: str) -> tuple[dict[str, object], dict[str, str]]:
        token_suffix = uuid4().hex[:10]
        payload = {
            "username": f"{prefix}_{token_suffix}",
            "email": f"{prefix}_{token_suffix}@example.com",
            "password": "Aa12345678",
        }
        response = client.post("/persona-api/auth/register", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        return data["user"], headers

    def _cleanup_user(self, user_id: int | None) -> None:
        if user_id is None:
            return
        with SessionLocal() as db:
            db.query(User).filter(User.id == user_id).delete()
            db.commit()

    def test_my_seeds_round_trip_persists_and_loads_same_payload(self):
        created_id: int | None = None
        user_id: int | None = None

        payload = {
            "create_type": "self_unified",
            "group": "self",
            "source_repo": "self-skill+nuwa-skill+forge-skill+digital-life",
            "display_name": "我的人格",
            "create_mode": "standard",
            "input_mode": "manual_profile",
            "input_modes": ["manual_profile", "documents"],
            "schema_key": "self_unified",
            "form_data": {
                "name": "我的人格",
                "create_mode": "standard",
                "input_modes": ["manual_profile", "documents"],
                "work_system_summary": "先把重要的事情做好。",
                "work_system_points": "先看目标\n再看路径",
                "reply_persona_summary": "回答时更清楚一点。",
                "reply_persona_points": "先说结论\n再补理由",
                "thinking_dna_summary": "先判断条件，再决定下一步。",
                "thinking_dna_points": "先问条件\n再看出路\n再算代价",
                "memory_evidence_summary": "把过去写过的话整理进去。",
                "memory_evidence_points": "聊天记录片段\n文字材料",
                "reflection_rules_summary": "保留边界，不替自己下定论。",
                "reflection_rules_points": "不夸张\n不越界",
            },
        }

        try:
            with TestClient(app) as client:
                user, headers = self._register_test_user(client, "my-seeds-self")
                user_id = int(user["id"])
                draft_response = client.post("/persona-api/create-wizard/draft", json=payload)
                self.assertEqual(draft_response.status_code, 200)
                draft = draft_response.json()["draft"]

                save_response = client.post(
                    "/persona-api/my-seeds",
                    headers=headers,
                    json={
                        "draft": draft,
                        "source_type": "create_wizard",
                        "status": "saved",
                    },
                )
                self.assertEqual(save_response.status_code, 200)
                saved = save_response.json()
                created_id = saved["id"]
                self.assertIn("material_summary", saved)
                self.assertTrue(saved["material_summary"])
                list_response = client.get("/persona-api/my-seeds", headers=headers)
                self.assertEqual(list_response.status_code, 200)
                seeds = list_response.json()
                self.assertTrue(any(item["id"] == created_id for item in seeds))

                detail_response = client.get(f"/persona-api/my-seeds/{created_id}", headers=headers)
                self.assertEqual(detail_response.status_code, 200)
                detail = detail_response.json()
                self.assertEqual(detail["id"], created_id)
                self.assertEqual(detail["slug"], saved["slug"])
                self.assertEqual(detail["name"], saved["name"])
                self.assertEqual(detail["draft_payload"]["meta"]["slug"], saved["slug"])
                self.assertEqual(detail["draft_payload"]["meta"]["create_type"], "self_unified")
                self.assertIn("self_persona_unified", detail["draft_payload"])
                self.assertEqual(detail["draft_payload"]["profile"], draft["profile"])
                self.assertEqual(detail["material_summary"], saved["material_summary"])

                persona_response = client.get(f"/persona-api/personas/{saved['slug']}", headers=headers)
                self.assertEqual(persona_response.status_code, 200)
                persona = persona_response.json()
                self.assertEqual(persona["slug"], saved["slug"])
                self.assertEqual(persona["name"], saved["name"])

                with patch("app.services.chat_service.generate_reply") as fake_reply:
                    fake_reply.return_value = {
                        "content": "已接收",
                        "model": "gpt-admin-test",
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                        "latency_ms": 1,
                    }
                    chat_response = client.post(
                        "/persona-api/chat",
                        headers=headers,
                        json={
                            "persona_slug": saved["slug"],
                            "session_id": None,
                            "message": "你好",
                        },
                    )

                self.assertEqual(chat_response.status_code, 200)
                chat_body = chat_response.json()
                self.assertEqual(chat_body["persona_slug"], saved["slug"])
                self.assertTrue(chat_body["reply"])
        finally:
            if created_id is not None:
                with SessionLocal() as db:
                    db.query(CreatedPersona).filter(CreatedPersona.id == created_id).delete()
                    db.commit()
            self._cleanup_user(user_id)

    def test_source_persona_seed_round_trip_persists_and_loads_material_summary(self):
        created_id: int | None = None
        user_id: int | None = None

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

        try:
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
                    user, headers = self._register_test_user(client, "my-seeds-source")
                    user_id = int(user["id"])
                    draft_response = client.post("/persona-api/create-wizard/draft", json=payload)
                    self.assertEqual(draft_response.status_code, 200)
                    draft = draft_response.json()["draft"]

                    save_response = client.post(
                        "/persona-api/my-seeds",
                        headers=headers,
                        json={
                            "draft": draft,
                            "source_type": "create_wizard",
                            "status": "saved",
                        },
                    )
                    self.assertEqual(save_response.status_code, 200)
                    saved = save_response.json()
                    created_id = saved["id"]
                    self.assertIn("material_summary", saved)
                    self.assertIn("图片材料", saved["material_summary"])

                    detail_response = client.get(f"/persona-api/my-seeds/{created_id}", headers=headers)
                    self.assertEqual(detail_response.status_code, 200)
                    detail = detail_response.json()
                    self.assertEqual(detail["draft_payload"]["meta"]["create_type"], "source_persona")
                    self.assertEqual(detail["draft_payload"]["meta"]["schema_key"], "source_anyone_from_sources")
                    self.assertIn("raw_materials", detail["draft_payload"])
                    self.assertTrue(detail["draft_payload"]["raw_materials"]["uploaded_text_documents"])
                    self.assertTrue(detail["draft_payload"]["raw_materials"]["uploaded_image_documents"])
                    self.assertTrue(detail["draft_payload"]["raw_materials"]["ocr_extracted_texts"])
                    self.assertIn("OCR", detail["material_summary"])
                    self.assertEqual(detail["material_summary"], saved["material_summary"])

                    persona_response = client.get(f"/persona-api/personas/{saved['slug']}", headers=headers)
                    self.assertEqual(persona_response.status_code, 200)
                    persona = persona_response.json()
                    self.assertEqual(persona["slug"], saved["slug"])
                    self.assertEqual(persona["name"], saved["name"])
        finally:
            if created_id is not None:
                with SessionLocal() as db:
                    db.query(CreatedPersona).filter(CreatedPersona.id == created_id).delete()
                    db.commit()
            self._cleanup_user(user_id)

    def test_family_companion_seed_round_trip_persists_and_chats(self):
        created_id: int | None = None
        user_id: int | None = None

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
                    "most_common_topics": "总是聊吃饭和休息",
                    "comfort_style": "先接住情绪，再慢慢安慰",
                    "most_characteristic_event": "考试前陪我复习",
                    "repeated_phrases": "先别急\n慢慢来",
                    "care_habits": "会记得提醒我吃饭",
                    "most_common_reminders": "早点睡，别熬夜",
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
                    "image_notes_text": "老照片说明",
                    "photo_notes_text": "老照片说明",
                    "voice_notes_text": "语音提醒片段",
                },
            },
        }

        try:
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
                    user, headers = self._register_test_user(client, "my-seeds-family")
                    user_id = int(user["id"])
                    draft_response = client.post("/persona-api/create-wizard/draft", json=payload)
                    self.assertEqual(draft_response.status_code, 200)
                    draft = draft_response.json()["draft"]

                    save_response = client.post(
                        "/persona-api/my-seeds",
                        headers=headers,
                        json={
                            "draft": draft,
                            "source_type": "create_wizard",
                            "status": "saved",
                        },
                    )
                    self.assertEqual(save_response.status_code, 200)
                    saved = save_response.json()
                    created_id = saved["id"]
                    self.assertIn("material_summary", saved)
                    self.assertIn("图片材料", saved["material_summary"])
                    self.assertIn("family-notes.txt", saved["summary"])
                    self.assertIn("图片材料", saved["summary"])

                    list_response = client.get("/persona-api/my-seeds", headers=headers)
                    self.assertEqual(list_response.status_code, 200)
                    seeds = list_response.json()
                    self.assertTrue(any(item["id"] == created_id for item in seeds))

                    detail_response = client.get(f"/persona-api/my-seeds/{created_id}", headers=headers)
                    self.assertEqual(detail_response.status_code, 200)
                    detail = detail_response.json()
                    self.assertEqual(detail["draft_payload"]["meta"]["create_type"], "family_companion")
                    self.assertEqual(detail["draft_payload"]["meta"]["schema_key"], "family_companion_mother")
                    self.assertEqual(detail["draft_payload"]["relationship_type"], "妈妈")
                    self.assertEqual(detail["draft_payload"]["family_subtype"], "mother")
                    self.assertIn("emotion_rules", detail["draft_payload"])
                    self.assertTrue(detail["draft_payload"]["emotion_rules"]["summary"])
                    self.assertIn("raw_materials", detail["draft_payload"])
                    self.assertEqual(
                        detail["draft_payload"]["raw_materials"]["chat_history_text"],
                        "妈总是提醒我按时吃饭和休息",
                    )
                    self.assertIn(
                        "小时候一起写作业",
                        detail["draft_payload"]["raw_materials"]["memory_notes_text"],
                    )
                    self.assertIn(
                        "晚上陪你散步",
                        detail["draft_payload"]["raw_materials"]["memory_notes_text"],
                    )
                    self.assertIn(
                        "家书片段",
                        detail["draft_payload"]["raw_materials"]["text_materials_text"],
                    )
                    self.assertIn(
                        "日常聊天摘录",
                        detail["draft_payload"]["raw_materials"]["text_materials_text"],
                    )
                    self.assertEqual(
                        detail["draft_payload"]["raw_materials"]["image_notes_text"],
                        "老照片说明",
                    )
                    self.assertEqual(
                        detail["draft_payload"]["raw_materials"]["voice_notes_text"],
                        "语音提醒片段",
                    )
                    self.assertEqual(
                        detail["draft_payload"]["raw_materials"]["uploaded_text_documents"][0]["filename"],
                        "family-notes.txt",
                    )
                    self.assertEqual(
                        detail["draft_payload"]["raw_materials"]["uploaded_image_documents"][0]["filename"],
                        "family-photo.jpg",
                    )
                    self.assertEqual(
                        detail["draft_payload"]["raw_materials"]["uploaded_image_documents"][0]["mime_type"],
                        "image/jpeg",
                    )
                    self.assertEqual(
                        detail["draft_payload"]["raw_materials"]["uploaded_image_documents"][0]["ocr_status"],
                        "success",
                    )
                    self.assertIn(
                        "先别急",
                        detail["draft_payload"]["raw_materials"]["uploaded_image_documents"][0]["ocr_text"],
                    )
                    self.assertTrue(detail["draft_payload"]["raw_materials"]["ocr_extracted_texts"])
                    self.assertIn("OCR", detail["material_summary"])
                    self.assertIn(
                        "先别急",
                        detail["draft_payload"]["raw_materials"]["ocr_extracted_texts"][0]["ocr_text"],
                    )
                    self.assertIn(
                        "小时候一起写作业",
                        " ".join(detail["draft_payload"]["memory_base"]["memory_fragments"]),
                    )
                    self.assertIn(
                        "先别急",
                        " ".join(detail["draft_payload"]["memory_base"]["procedural_memories"]),
                    )
                    self.assertIn("按时吃饭和休息", detail["draft_payload"]["memory_base"]["chat_history_summary"])
                    self.assertTrue(detail["draft_payload"]["memory_base"]["episodic_memories"])
                    self.assertTrue(detail["draft_payload"]["memory_base"]["semantic_memories"])
                    self.assertTrue(detail["draft_payload"]["memory_base"]["procedural_memories"])
                    self.assertEqual(
                        detail["draft_payload"]["guided_memory_answers"]["most_common_topics"],
                        "总是聊吃饭和休息",
                    )
                    self.assertTrue(detail["draft_payload"]["raw_materials"]["uploaded_text_documents"])
                    self.assertIn("三层记忆", saved["summary"])
                    self.assertIn("引导补充", saved["summary"])
                    self.assertIn("OCR识别", saved["summary"])
                    self.assertIn("妈妈", detail["summary"])

                    persona_response = client.get(f"/persona-api/personas/{saved['slug']}", headers=headers)
                    self.assertEqual(persona_response.status_code, 200)
                    persona = persona_response.json()
                    self.assertEqual(persona["slug"], saved["slug"])
                    self.assertIn("家人陪伴", persona.get("category", ""))

                    with patch("app.services.chat_service.generate_reply") as fake_reply:
                        fake_reply.return_value = {
                            "content": "我在呢",
                            "model": "gpt-admin-test",
                            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                            "latency_ms": 1,
                        }
                        chat_response = client.post(
                            "/persona-api/chat",
                            headers=headers,
                            json={
                                "persona_slug": saved["slug"],
                                "session_id": None,
                                "message": "我今天有点累",
                            },
                        )

                    self.assertEqual(chat_response.status_code, 200)
                    chat_body = chat_response.json()
                    self.assertEqual(chat_body["persona_slug"], saved["slug"])
                    self.assertTrue(chat_body["reply"])
        finally:
            if created_id is not None:
                with SessionLocal() as db:
                    db.query(CreatedPersona).filter(CreatedPersona.id == created_id).delete()
                    db.commit()
            self._cleanup_user(user_id)

    def test_reunion_persona_seed_round_trip_persists_and_chats(self):
        created_id: int | None = None
        user_id: int | None = None

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
                            "size": 2048,
                            "data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+3d8AAAAASUVORK5CYII=",
                        }
                    ],
                    "ocr_extracted_texts": [
                        {
                            "filename": "reunion-shot.png",
                            "mime_type": "image/png",
                            "size": 2048,
                            "ocr_text": "旧截图里的话：先慢慢回忆",
                            "ocr_status": "success",
                        }
                    ],
                    "photo_notes_text": "照片里的关键场景说明",
                    "voice_notes_text": "口述回忆片段",
                },
            },
        }

        try:
            with TestClient(app) as client:
                user, headers = self._register_test_user(client, "my-seeds-reunion")
                user_id = int(user["id"])
                draft_response = client.post("/persona-api/create-wizard/draft", json=payload)
                self.assertEqual(draft_response.status_code, 200)
                draft = draft_response.json()["draft"]

                save_response = client.post(
                    "/persona-api/my-seeds",
                    headers=headers,
                    json={
                        "draft": draft,
                        "source_type": "create_wizard",
                        "status": "saved",
                    },
                )
                self.assertEqual(save_response.status_code, 200)
                saved = save_response.json()
                created_id = saved["id"]
                self.assertIn("material_summary", saved)
                self.assertTrue(saved["material_summary"])
                self.assertIn("引导补充", saved["summary"])
                self.assertIn("三层记忆", saved["summary"])
                self.assertIn("重逢人格", saved["summary"])

                list_response = client.get("/persona-api/my-seeds", headers=headers)
                self.assertEqual(list_response.status_code, 200)
                seeds = list_response.json()
                self.assertTrue(any(item["id"] == created_id for item in seeds))

                detail_response = client.get(f"/persona-api/my-seeds/{created_id}", headers=headers)
                self.assertEqual(detail_response.status_code, 200)
                detail = detail_response.json()
                self.assertEqual(detail["draft_payload"]["meta"]["create_type"], "reunion_persona")
                self.assertEqual(detail["draft_payload"]["meta"]["schema_key"], "reunion_persona_chat_history")
                self.assertEqual(detail["draft_payload"]["relationship_type"], "重逢人格")
                self.assertIn("raw_materials", detail["draft_payload"])
                self.assertTrue(detail["draft_payload"]["raw_materials"]["uploaded_text_documents"])
                self.assertTrue(detail["draft_payload"]["raw_materials"]["uploaded_image_documents"])
                self.assertTrue(detail["draft_payload"]["raw_materials"]["ocr_extracted_texts"])
                self.assertTrue(detail["draft_payload"]["reunion_memory_base"]["episodic_memories"])
                self.assertTrue(detail["draft_payload"]["reunion_memory_base"]["semantic_memories"])
                self.assertTrue(detail["draft_payload"]["reunion_memory_base"]["procedural_memories"])
                self.assertGreaterEqual(detail["draft_payload"]["reunion_memory_base"]["episodic_count"], 1)
                self.assertGreaterEqual(detail["draft_payload"]["reunion_memory_base"]["semantic_count"], 1)
                self.assertGreaterEqual(detail["draft_payload"]["reunion_memory_base"]["procedural_count"], 1)
                self.assertIn("reunion_guided_memory_answers", detail["draft_payload"])
                self.assertEqual(
                    detail["draft_payload"]["reunion_guided_memory_answers"]["recall_scenes"],
                    "路过旧街道时最容易想起",
                )
                self.assertIsNotNone(detail["draft_payload"]["reunion_memory_retrieval_policy"])
                self.assertIsNotNone(detail["draft_payload"]["reunion_safety_guardrails"])
                self.assertEqual(detail["material_summary"], saved["material_summary"])

                persona_response = client.get(f"/persona-api/personas/{saved['slug']}", headers=headers)
                self.assertEqual(persona_response.status_code, 200)
                persona = persona_response.json()
                self.assertEqual(persona["slug"], saved["slug"])
                self.assertIn("重逢人格", persona.get("category", ""))

                with patch("app.services.chat_service.generate_reply") as fake_reply:
                    fake_reply.return_value = {
                        "content": "我在呢",
                        "model": "gpt-admin-test",
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                        "latency_ms": 1,
                    }
                    chat_response = client.post(
                        "/persona-api/chat",
                        headers=headers,
                        json={
                            "persona_slug": saved["slug"],
                            "session_id": None,
                            "message": "我有点想念以前",
                        },
                    )

                self.assertEqual(chat_response.status_code, 200)
                chat_body = chat_response.json()
                self.assertEqual(chat_body["persona_slug"], saved["slug"])
                self.assertTrue(chat_body["reply"])
        finally:
            if created_id is not None:
                with SessionLocal() as db:
                    db.query(CreatedPersona).filter(CreatedPersona.id == created_id).delete()
                    db.commit()
            self._cleanup_user(user_id)

    def test_family_companion_guided_answers_without_materials_still_builds_layers(self):
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
                    "most_common_topics": "常聊吃饭和休息",
                    "comfort_style": "先接住情绪，再慢慢安慰",
                    "most_characteristic_event": "总在考试前陪我复习",
                    "repeated_phrases": "慢慢来\n别急",
                    "care_habits": "会记得我生病时的照顾方式",
                    "most_common_reminders": "按时吃饭和早点睡",
                },
            },
        }

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        draft = response.json()["draft"]
        self.assertEqual(draft["family_subtype"], "mother")
        self.assertEqual(draft["guided_memory_answers"]["most_common_topics"], "常聊吃饭和休息")
        self.assertTrue(draft["memory_base"]["episodic_memories"])
        self.assertTrue(draft["memory_base"]["semantic_memories"])
        self.assertTrue(draft["memory_base"]["procedural_memories"])

    def test_intimate_companion_seed_round_trip_persists_and_chats(self):
        created_id: int | None = None
        user_id: int | None = None

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

        try:
            with TestClient(app) as client:
                user, headers = self._register_test_user(client, "my-seeds-intimate")
                user_id = int(user["id"])
                draft_response = client.post("/persona-api/create-wizard/draft", json=payload)
                self.assertEqual(draft_response.status_code, 200)
                draft = draft_response.json()["draft"]

                save_response = client.post(
                    "/persona-api/my-seeds",
                    headers=headers,
                    json={
                        "draft": draft,
                        "source_type": "create_wizard",
                        "status": "saved",
                    },
                )
                self.assertEqual(save_response.status_code, 200)
                saved = save_response.json()
                created_id = saved["id"]
                self.assertIn("material_summary", saved)
                self.assertTrue(saved["material_summary"])

                detail_response = client.get(f"/persona-api/my-seeds/{created_id}", headers=headers)
                self.assertEqual(detail_response.status_code, 200)
                detail = detail_response.json()
                self.assertEqual(detail["draft_payload"]["meta"]["create_type"], "intimate_companion")
                self.assertEqual(detail["draft_payload"]["meta"]["schema_key"], "intimate_companion_relationship_understanding")
                self.assertEqual(detail["draft_payload"]["relationship_type"], "关系理解")
                self.assertIn("raw_materials", detail["draft_payload"])
                self.assertTrue(detail["draft_payload"]["raw_materials"]["uploaded_text_documents"])
                self.assertTrue(detail["draft_payload"]["raw_materials"]["uploaded_image_documents"])
                self.assertTrue(detail["draft_payload"]["raw_materials"]["ocr_extracted_texts"])
                self.assertEqual(detail["material_summary"], saved["material_summary"])

                persona_response = client.get(f"/persona-api/personas/{saved['slug']}", headers=headers)
                self.assertEqual(persona_response.status_code, 200)
                persona = persona_response.json()
                self.assertEqual(persona["slug"], saved["slug"])
                self.assertIn("亲密关系", persona.get("category", ""))

                with patch("app.services.chat_service.generate_reply") as fake_reply:
                    fake_reply.return_value = {
                        "content": "我在听",
                        "model": "gpt-admin-test",
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                        "latency_ms": 1,
                    }
                    chat_response = client.post(
                        "/persona-api/chat",
                        headers=headers,
                        json={
                            "persona_slug": saved["slug"],
                            "session_id": None,
                            "message": "我今天有点烦",
                        },
                    )

                self.assertEqual(chat_response.status_code, 200)
                chat_body = chat_response.json()
                self.assertEqual(chat_body["persona_slug"], saved["slug"])
                self.assertTrue(chat_body["reply"])
        finally:
            if created_id is not None:
                with SessionLocal() as db:
                    db.query(CreatedPersona).filter(CreatedPersona.id == created_id).delete()
                    db.commit()
            self._cleanup_user(user_id)


if __name__ == "__main__":
    unittest.main()
