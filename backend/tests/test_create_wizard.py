from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from main import app


class CreateWizardTests(unittest.TestCase):
    def test_create_wizard_draft_endpoint_builds_self_persona_draft(self):
        payload = {
            "create_type": "self_persona",
            "input_mode": "manual_profile",
            "form_data": {
                "name": "更理性的我",
                "intro": "先把自己说清楚",
                "values": "结果和边界",
                "decision_priority": "先看可执行性",
                "expression_style": "简洁直接",
                "boundaries": "不越界",
            },
        }

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("draft", body)
        self.assertEqual(body["draft"]["meta"]["create_type"], "self_persona")
        self.assertEqual(body["draft"]["meta"]["name"], "更理性的我")
        self.assertTrue(body["draft"]["mindset"].strip())
        self.assertTrue(body["draft"]["guardrails"].strip())

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
