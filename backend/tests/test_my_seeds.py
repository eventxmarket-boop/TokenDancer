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
            "create_type": "relationship_persona",
            "input_mode": "colleague",
            "form_data": {
                "relationship_type": "同事",
                "persona_name": "产品同事",
                "speech_style": "说话直接，先讲结论",
                "decision_logic": "先看时间成本和协作成本",
                "purpose": "帮助理解这位同事的表达方式",
                "relation_boundaries": "不越界，不臆测未说出的事实",
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
                self.assertEqual(detail["draft_payload"]["meta"]["create_type"], draft["meta"]["create_type"])
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
            "source_repo": "MamaSkill+parents-skills+darwin-skill",
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
