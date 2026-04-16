from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services import ocr_service


class OcrServiceTests(unittest.TestCase):
    def setUp(self):
        self.sample_image = {
            "filename": "chat-shot.png",
            "mime_type": "image/png",
            "size": 1024,
            "data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+3d8AAAAASUVORK5CYII=",
        }

    def test_normalize_ocr_text_compacts_whitespace(self):
        self.assertEqual(ocr_service.normalize_ocr_text("  先别急   \n  慢慢来  "), "先别急\n慢慢来")

    def test_extract_text_from_image_success_uses_first_extractor(self):
        with patch("app.services.ocr_service._extract_with_rapidocr", return_value="  先别急  \n 慢慢来  "), patch(
            "app.services.ocr_service._extract_with_pytesseract", return_value=""
        ), patch("app.services.ocr_service._extract_with_tesseract_cli", return_value=""):
            result = ocr_service.extract_text_from_image(self.sample_image)

        self.assertEqual(result["filename"], "chat-shot.png")
        self.assertEqual(result["mime_type"], "image/png")
        self.assertEqual(result["ocr_status"], "success")
        self.assertEqual(result["ocr_text"], "先别急\n慢慢来")

    def test_extract_text_from_image_failure_returns_failed(self):
        with patch("app.services.ocr_service._extract_with_rapidocr", return_value=""), patch(
            "app.services.ocr_service._extract_with_pytesseract", return_value=""
        ), patch("app.services.ocr_service._extract_with_tesseract_cli", return_value=""):
            result = ocr_service.extract_text_from_image(self.sample_image)

        self.assertEqual(result["filename"], "chat-shot.png")
        self.assertEqual(result["ocr_status"], "failed")
        self.assertEqual(result["ocr_text"], "")

    def test_extract_texts_from_uploaded_images_handles_mixed_results(self):
        with patch("app.services.ocr_service.extract_text_from_image") as mock_extract:
            mock_extract.side_effect = [
                {"filename": "a.png", "mime_type": "image/png", "size": 1, "ocr_text": "甲", "ocr_status": "success"},
                {"filename": "b.png", "mime_type": "image/png", "size": 1, "ocr_text": "", "ocr_status": "failed"},
            ]
            results = ocr_service.extract_texts_from_uploaded_images(
                [
                    {"filename": "a.png", "mime_type": "image/png", "size": 1, "data_url": "data:image/png;base64,AA=="},
                    {"filename": "b.png", "mime_type": "image/png", "size": 1, "data_url": "data:image/png;base64,AA=="},
                ]
            )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["ocr_status"], "success")
        self.assertEqual(results[1]["ocr_status"], "failed")


if __name__ == "__main__":
    unittest.main()
