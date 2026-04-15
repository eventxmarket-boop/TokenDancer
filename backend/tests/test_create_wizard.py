from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from main import app


class CreateWizardTests(unittest.TestCase):
    def test_create_wizard_draft_endpoint_builds_self_persona_draft(self):
        payload = {
            "create_type": "self_persona",
            "group": "self",
            "source_repo": "self-skill",
            "display_name": "更理性的我",
            "input_mode": "manual_profile",
            "schema_key": "self_persona",
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
        self.assertEqual(body["draft"]["meta"]["display_name"], "更理性的我")
        self.assertEqual(body["draft"]["meta"]["group"], "self")
        self.assertEqual(body["draft"]["meta"]["source_repo"], "self-skill")
        self.assertEqual(body["draft"]["meta"]["schema_key"], "self_persona")
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
