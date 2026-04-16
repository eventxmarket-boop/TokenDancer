from __future__ import annotations

import unittest
from uuid import uuid4
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.created_persona import CreatedPersona
from app.models.user import User
from main import app


class AuthClosureTests(unittest.TestCase):
    def test_register_login_me_and_user_scoped_seed_visibility(self):
        created_id: int | None = None
        user1_id: int | None = None
        user2_id: int | None = None

        username = f"auth_user_{uuid4().hex[:8]}"
        email = f"{username}@example.com"
        password = "Aa12345678"

        other_username = f"auth_peer_{uuid4().hex[:8]}"
        other_email = f"{other_username}@example.com"
        other_password = "Bb12345678"

        draft_payload = {
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
                register_response = client.post(
                    "/persona-api/auth/register",
                    json={
                        "username": username,
                        "email": email,
                        "password": password,
                    },
                )
                self.assertEqual(register_response.status_code, 200)
                register_body = register_response.json()
                user1_id = int(register_body["user"]["id"])
                self.assertTrue(register_body["access_token"])

                me_response = client.get(
                    "/persona-api/auth/me",
                    headers={"Authorization": f"Bearer {register_body['access_token']}"},
                )
                self.assertEqual(me_response.status_code, 200)
                me_body = me_response.json()
                self.assertEqual(me_body["id"], user1_id)
                self.assertEqual(me_body["username"], username)

                login_response = client.post(
                    "/persona-api/auth/login",
                    json={
                        "username_or_email": username,
                        "password": password,
                    },
                )
                self.assertEqual(login_response.status_code, 200)
                login_body = login_response.json()
                token = login_body["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                other_register_response = client.post(
                    "/persona-api/auth/register",
                    json={
                        "username": other_username,
                        "email": other_email,
                        "password": other_password,
                    },
                )
                self.assertEqual(other_register_response.status_code, 200)
                other_body = other_register_response.json()
                user2_id = int(other_body["user"]["id"])
                other_headers = {"Authorization": f"Bearer {other_body['access_token']}"}

                draft_response = client.post("/persona-api/create-wizard/draft", json=draft_payload)
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
                created_id = int(saved["id"])

                own_list_response = client.get("/persona-api/my-seeds", headers=headers)
                self.assertEqual(own_list_response.status_code, 200)
                own_list = own_list_response.json()
                self.assertTrue(any(item["id"] == created_id for item in own_list))

                other_list_response = client.get("/persona-api/my-seeds", headers=other_headers)
                self.assertEqual(other_list_response.status_code, 200)
                other_list = other_list_response.json()
                self.assertFalse(any(item["id"] == created_id for item in other_list))

                own_detail_response = client.get(
                    f"/persona-api/my-seeds/{created_id}",
                    headers=headers,
                )
                self.assertEqual(own_detail_response.status_code, 200)

                other_detail_response = client.get(
                    f"/persona-api/my-seeds/{created_id}",
                    headers=other_headers,
                )
                self.assertEqual(other_detail_response.status_code, 404)

                own_persona_response = client.get(
                    f"/persona-api/personas/{saved['slug']}",
                    headers=headers,
                )
                self.assertEqual(own_persona_response.status_code, 200)

                other_persona_response = client.get(
                    f"/persona-api/personas/{saved['slug']}",
                    headers=other_headers,
                )
                self.assertEqual(other_persona_response.status_code, 404)

                with patch("app.services.chat_service.generate_reply") as fake_reply:
                    fake_reply.return_value = {
                        "content": "你好，我在。",
                        "model": "fake-model",
                        "usage": {
                            "prompt_tokens": 1,
                            "completion_tokens": 2,
                            "total_tokens": 3,
                        },
                        "latency_ms": 5,
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

                    other_chat_response = client.post(
                        "/persona-api/chat",
                        headers=other_headers,
                        json={
                            "persona_slug": saved["slug"],
                            "session_id": None,
                            "message": "你好",
                        },
                    )
                    self.assertEqual(other_chat_response.status_code, 404)
        finally:
            with SessionLocal() as db:
                if created_id is not None:
                    db.query(CreatedPersona).filter(CreatedPersona.id == created_id).delete()
                if user1_id is not None:
                    db.query(User).filter(User.id == user1_id).delete()
                if user2_id is not None:
                    db.query(User).filter(User.id == user2_id).delete()
                db.commit()


if __name__ == "__main__":
    unittest.main()
