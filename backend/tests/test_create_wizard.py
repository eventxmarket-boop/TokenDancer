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

    def test_create_wizard_draft_endpoint_builds_family_companion_draft(self):
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

        with TestClient(app) as client:
            response = client.post("/persona-api/create-wizard/draft", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["draft"]["meta"]["create_type"], "family_companion")
        self.assertEqual(body["draft"]["meta"]["group"], "relationship_family")
        self.assertEqual(body["draft"]["meta"]["source_repo"], "MamaSkill+parents-skills+darwin-skill")
        self.assertEqual(body["draft"]["meta"]["display_name"], "家人陪伴")
        self.assertEqual(body["draft"]["meta"]["input_mode"], "mother")
        self.assertEqual(body["draft"]["meta"]["schema_key"], "family_companion_mother")
        self.assertEqual(body["draft"]["relationship_type"], "妈妈")
        self.assertIsNotNone(body["draft"]["persona_profile"])
        self.assertIsNotNone(body["draft"]["memory_base"])
        self.assertIn("家人陪伴", body["draft"]["profile"])
        self.assertIn("妈妈", body["draft"]["profile"])

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
