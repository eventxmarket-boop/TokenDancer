from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.config import settings
from app.services.openai_image_service import generate_image_base64
from main import app


class ImageLabTests(unittest.TestCase):
    def test_generate_image_base64_uses_injected_client(self):
        fake_result = SimpleNamespace(data=[SimpleNamespace(b64_json="QUJDRA==")])
        fake_client = SimpleNamespace(images=SimpleNamespace(generate=MagicMock(return_value=fake_result)))

        result = generate_image_base64(
            "a clean product shot of a red apple on a wooden table",
            size="1024x1536",
            quality="high",
            output_format="webp",
            user_id="internal-test-user",
            client=fake_client,
        )

        self.assertEqual(result["image_base64"], "QUJDRA==")
        self.assertEqual(result["mime_type"], "image/webp")
        self.assertEqual(result["model"], settings.OPENAI_IMAGE_MODEL)
        self.assertEqual(result["size"], "1024x1536")
        self.assertEqual(result["quality"], "high")
        self.assertEqual(result["output_format"], "webp")
        fake_client.images.generate.assert_called_once()
        called_kwargs = fake_client.images.generate.call_args.kwargs
        self.assertEqual(called_kwargs["model"], settings.OPENAI_IMAGE_MODEL)
        self.assertEqual(called_kwargs["prompt"], "a clean product shot of a red apple on a wooden table")
        self.assertEqual(called_kwargs["size"], "1024x1536")
        self.assertEqual(called_kwargs["quality"], "high")
        self.assertEqual(called_kwargs["output_format"], "webp")
        self.assertEqual(called_kwargs["user"], "internal-test-user")

    def test_generate_route_returns_expected_payload(self):
        fake_payload = {
            "image_base64": "QUJDRA==",
            "mime_type": "image/png",
            "model": "gpt-image-2",
            "size": "1024x1024",
            "quality": "medium",
            "output_format": "png",
        }

        with patch("app.routers.image_lab.generate_image_base64", return_value=fake_payload):
            with TestClient(app) as client:
                response = client.post(
                    "/persona-api/image-lab/generate",
                    json={
                        "prompt": "a simple red apple on a wooden table",
                        "size": "1024x1024",
                        "quality": "medium",
                        "output_format": "png",
                    },
                    headers={"X-Internal-User": "internal-test-user"},
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["image_base64"], "QUJDRA==")
        self.assertEqual(body["mime_type"], "image/png")
        self.assertEqual(body["model"], "gpt-image-2")
        self.assertEqual(body["size"], "1024x1024")
        self.assertEqual(body["quality"], "medium")
        self.assertEqual(body["output_format"], "png")

    def test_generate_route_rejects_short_prompt(self):
        with TestClient(app) as client:
            response = client.post(
                "/persona-api/image-lab/generate",
                json={
                    "prompt": "hi",
                    "size": "1024x1024",
                    "quality": "medium",
                    "output_format": "png",
                },
            )

        self.assertEqual(response.status_code, 422)

    def test_generate_route_masks_internal_exception(self):
        with patch("app.routers.image_lab.generate_image_base64", side_effect=RuntimeError("traceback detail")):
            with TestClient(app) as client:
                response = client.post(
                    "/persona-api/image-lab/generate",
                    json={
                        "prompt": "a simple red apple on a wooden table",
                        "size": "1024x1024",
                        "quality": "medium",
                        "output_format": "png",
                    },
                )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "图片生成失败，请稍后重试。")


if __name__ == "__main__":
    unittest.main()
