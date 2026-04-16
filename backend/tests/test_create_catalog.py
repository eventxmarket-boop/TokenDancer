from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from main import app


class CreateCatalogTests(unittest.TestCase):
    def test_create_catalog_endpoint_returns_grouped_create_modes(self):
        with TestClient(app) as client:
            response = client.get("/persona-api/create-catalog")

        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("groups", payload)
        self.assertGreaterEqual(len(payload["groups"]), 5)

        groups = {group["group"]: group for group in payload["groups"]}
        self.assertIn("self", groups)
        self.assertIn("source", groups)
        self.assertIn("digital_twin", groups)
        self.assertIn("protection", groups)

        self.assertEqual(len(groups["self"]["items"]), 1)
        self.assertEqual(groups["self"]["items"][0]["create_type"], "self_unified")
        self.assertEqual(
            groups["self"]["items"][0]["source_repo"],
            "self-skill+nuwa-skill+forge-skill+digital-life",
        )
        self.assertTrue(
            any(
                item["repo_url"] == "https://github.com/moyitech/self-skill"
                for item in groups["self"]["items"]
            )
        )

        self.assertIn("relationship_family", groups)
        family_items = groups["relationship_family"]["items"]
        family_slugs = {item["slug"] for item in family_items}
        self.assertIn("family_companion", family_slugs)
        self.assertIn("reunion_persona", family_slugs)
        family_item = next(item for item in family_items if item["slug"] == "family_companion")
        self.assertEqual(family_item["source_repo"], "parents-skills+MamaSkill")
        self.assertIn("https://github.com/xiaoheizi8/parents-skills", family_item["source_urls"])
        reunion_item = next(item for item in family_items if item["slug"] == "reunion_persona")
        self.assertEqual(reunion_item["source_repo"], "reunion-skill")
        self.assertIn("https://github.com/yangdongchen66-boop/reunion-skill", reunion_item["source_urls"])

        self.assertIn("relationship_intimate", groups)
        intimate_items = groups["relationship_intimate"]["items"]
        intimate_items_by_slug = {item["slug"]: item for item in intimate_items}
        self.assertIn("relationship_management", intimate_items_by_slug)
        self.assertEqual(
            intimate_items_by_slug["relationship_management"]["source_urls"],
            [
                "https://github.com/TammyTan516/relationship-training-skill",
                "https://github.com/kroxchan/xinyi",
                "https://github.com/NatalieCao323/partner-skill",
                "https://github.com/wwwttlll/npy-skill",
            ],
        )
        self.assertEqual(
            intimate_items_by_slug["message_simulation"]["source_urls"],
            ["https://github.com/yyyyyyylll/crush-skill"],
        )
        self.assertEqual(
            intimate_items_by_slug["past_relation_mirror"]["source_urls"],
            [
                "https://github.com/titanwings/ex-skill",
                "https://github.com/z969081067-commits/first-love-skill",
                "https://github.com/Cyh29hao/shuixian-skill",
            ],
        )


if __name__ == "__main__":
    unittest.main()
