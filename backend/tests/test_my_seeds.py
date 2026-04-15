from __future__ import annotations

import unittest

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
        finally:
            if created_id is not None:
                with SessionLocal() as db:
                    db.query(CreatedPersona).filter(CreatedPersona.id == created_id).delete()
                    db.commit()


if __name__ == "__main__":
    unittest.main()
