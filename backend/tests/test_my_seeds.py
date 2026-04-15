from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.created_persona import CreatedPersona
from main import app


class MySeedsTests(unittest.TestCase):
    def test_my_seeds_round_trip_persists_and_loads_same_payload(self):
        created_id: int | None = None

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
                draft_response = client.post("/persona-api/create-wizard/draft", json=payload)
                self.assertEqual(draft_response.status_code, 200)
                draft = draft_response.json()["draft"]

                save_response = client.post(
                    "/persona-api/my-seeds",
                    json={
                        "draft": draft,
                        "source_type": "create_wizard",
                        "status": "saved",
                    },
                )
                self.assertEqual(save_response.status_code, 200)
                saved = save_response.json()
                created_id = saved["id"]

                list_response = client.get("/persona-api/my-seeds")
                self.assertEqual(list_response.status_code, 200)
                seeds = list_response.json()
                self.assertTrue(any(item["id"] == created_id for item in seeds))

                detail_response = client.get(f"/persona-api/my-seeds/{created_id}")
                self.assertEqual(detail_response.status_code, 200)
                detail = detail_response.json()
                self.assertEqual(detail["id"], created_id)
                self.assertEqual(detail["slug"], saved["slug"])
                self.assertEqual(detail["name"], saved["name"])
                self.assertEqual(detail["draft_payload"]["meta"]["slug"], saved["slug"])
                self.assertEqual(detail["draft_payload"]["meta"]["create_type"], "self_unified")
                self.assertIn("self_persona_unified", detail["draft_payload"])
                self.assertEqual(detail["draft_payload"]["profile"], draft["profile"])

                persona_response = client.get(f"/persona-api/personas/{saved['slug']}")
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

    def test_family_companion_seed_round_trip_persists_and_chats(self):
        created_id: int | None = None

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
            },
        }

        try:
            with TestClient(app) as client:
                draft_response = client.post("/persona-api/create-wizard/draft", json=payload)
                self.assertEqual(draft_response.status_code, 200)
                draft = draft_response.json()["draft"]

                save_response = client.post(
                    "/persona-api/my-seeds",
                    json={
                        "draft": draft,
                        "source_type": "create_wizard",
                        "status": "saved",
                    },
                )
                self.assertEqual(save_response.status_code, 200)
                saved = save_response.json()
                created_id = saved["id"]

                list_response = client.get("/persona-api/my-seeds")
                self.assertEqual(list_response.status_code, 200)
                seeds = list_response.json()
                self.assertTrue(any(item["id"] == created_id for item in seeds))

                detail_response = client.get(f"/persona-api/my-seeds/{created_id}")
                self.assertEqual(detail_response.status_code, 200)
                detail = detail_response.json()
                self.assertEqual(detail["draft_payload"]["meta"]["create_type"], "family_companion")
                self.assertEqual(detail["draft_payload"]["meta"]["schema_key"], "family_companion_mother")
                self.assertEqual(detail["draft_payload"]["relationship_type"], "妈妈")

                persona_response = client.get(f"/persona-api/personas/{saved['slug']}")
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

    def test_reunion_persona_seed_round_trip_persists_and_chats(self):
        created_id: int | None = None

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
            },
        }

        try:
            with TestClient(app) as client:
                draft_response = client.post("/persona-api/create-wizard/draft", json=payload)
                self.assertEqual(draft_response.status_code, 200)
                draft = draft_response.json()["draft"]

                save_response = client.post(
                    "/persona-api/my-seeds",
                    json={
                        "draft": draft,
                        "source_type": "create_wizard",
                        "status": "saved",
                    },
                )
                self.assertEqual(save_response.status_code, 200)
                saved = save_response.json()
                created_id = saved["id"]

                list_response = client.get("/persona-api/my-seeds")
                self.assertEqual(list_response.status_code, 200)
                seeds = list_response.json()
                self.assertTrue(any(item["id"] == created_id for item in seeds))

                detail_response = client.get(f"/persona-api/my-seeds/{created_id}")
                self.assertEqual(detail_response.status_code, 200)
                detail = detail_response.json()
                self.assertEqual(detail["draft_payload"]["meta"]["create_type"], "reunion_persona")
                self.assertEqual(detail["draft_payload"]["meta"]["schema_key"], "reunion_persona_chat_history")
                self.assertEqual(detail["draft_payload"]["relationship_type"], "重逢人格")

                persona_response = client.get(f"/persona-api/personas/{saved['slug']}")
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

    def test_intimate_companion_seed_round_trip_persists_and_chats(self):
        created_id: int | None = None

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
            },
        }

        try:
            with TestClient(app) as client:
                draft_response = client.post("/persona-api/create-wizard/draft", json=payload)
                self.assertEqual(draft_response.status_code, 200)
                draft = draft_response.json()["draft"]

                save_response = client.post(
                    "/persona-api/my-seeds",
                    json={
                        "draft": draft,
                        "source_type": "create_wizard",
                        "status": "saved",
                    },
                )
                self.assertEqual(save_response.status_code, 200)
                saved = save_response.json()
                created_id = saved["id"]

                detail_response = client.get(f"/persona-api/my-seeds/{created_id}")
                self.assertEqual(detail_response.status_code, 200)
                detail = detail_response.json()
                self.assertEqual(detail["draft_payload"]["meta"]["create_type"], "intimate_companion")
                self.assertEqual(detail["draft_payload"]["meta"]["schema_key"], "intimate_companion_relationship_understanding")
                self.assertEqual(detail["draft_payload"]["relationship_type"], "关系理解")

                persona_response = client.get(f"/persona-api/personas/{saved['slug']}")
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


if __name__ == "__main__":
    unittest.main()
