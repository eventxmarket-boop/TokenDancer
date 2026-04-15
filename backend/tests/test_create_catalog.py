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

        self.assertGreaterEqual(len(groups["self"]["items"]), 4)
        self.assertEqual(groups["self"]["items"][0]["source_repo"], "self-skill")
        self.assertTrue(
            any(
                item["repo_url"] == "https://github.com/moyitech/self-skill"
                for item in groups["self"]["items"]
            )
        )


if __name__ == "__main__":
    unittest.main()
