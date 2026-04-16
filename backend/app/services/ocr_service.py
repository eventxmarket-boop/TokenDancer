from __future__ import annotations

import base64
import binascii
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote_to_bytes


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_multiline_text(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def _guess_suffix(filename: str, mime_type: str) -> str:
    name = _normalize_text(filename).lower()
    mime = _normalize_text(mime_type).lower()
    if name.endswith(".png") or mime.endswith("png"):
        return ".png"
    if name.endswith(".webp") or mime.endswith("webp"):
        return ".webp"
    if name.endswith(".jpeg") or name.endswith(".jpg") or mime.endswith("jpeg") or mime.endswith("jpg"):
        return ".jpg"
    if name.endswith(".bmp") or mime.endswith("bmp"):
        return ".bmp"
    if name.endswith(".gif") or mime.endswith("gif"):
        return ".gif"
    return ".png"


def _decode_data_url(data_url: str) -> bytes:
    text = _normalize_text(data_url)
    if not text.startswith("data:") or "," not in text:
        return b""
    header, payload = text.split(",", 1)
    if ";base64" in header:
        try:
            return base64.b64decode(payload, validate=False)
        except (ValueError, binascii.Error):
            return b""
    try:
        return unquote_to_bytes(payload)
    except Exception:
        return b""


def normalize_ocr_text(text: Any) -> str:
    return _normalize_multiline_text(text)


def _extract_with_rapidocr(image_path: str) -> str:
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore
    except Exception:
        return ""

    try:
        ocr = RapidOCR()
        result = ocr(image_path)
    except Exception:
        return ""

    raw_items = result[0] if isinstance(result, tuple) and result else result
    if not isinstance(raw_items, list):
        return ""

    lines: list[str] = []
    for item in raw_items:
        if isinstance(item, dict):
            text = _normalize_text(item.get("text") or item.get("ocr_text") or item.get("content"))
        elif isinstance(item, (list, tuple)):
            text = _normalize_text(item[1] if len(item) > 1 else item[0] if item else "")
        else:
            text = _normalize_text(item)
        if text:
            lines.append(text)
    return normalize_ocr_text("\n".join(lines))


def _extract_with_pytesseract(image_path: str) -> str:
    try:
        import pytesseract  # type: ignore
    except Exception:
        return ""

    try:
        return normalize_ocr_text(pytesseract.image_to_string(image_path, lang="chi_sim+eng"))
    except Exception:
        return ""


def _extract_with_tesseract_cli(image_path: str) -> str:
    if not shutil.which("tesseract"):
        return ""

    try:
        completed = subprocess.run(
            ["tesseract", image_path, "stdout", "-l", "chi_sim+eng"],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ""

    output = completed.stdout or completed.stderr or ""
    return normalize_ocr_text(output)


def extract_text_from_image(image_document: dict[str, Any]) -> dict[str, Any]:
    filename = _normalize_text(image_document.get("filename") or image_document.get("name"))
    mime_type = _normalize_text(image_document.get("mime_type") or image_document.get("type")) or "image/*"
    try:
        size = int(image_document.get("size") or 0)
    except (TypeError, ValueError):
        size = 0
    data_url = _normalize_text(image_document.get("data_url") or image_document.get("preview_url") or image_document.get("url"))

    ocr_status = "failed"
    ocr_text = ""
    temp_path = ""
    try:
        image_bytes = _decode_data_url(data_url)
        if not image_bytes:
            return {
                "filename": filename,
                "mime_type": mime_type,
                "size": max(size, 0),
                "ocr_text": "",
                "ocr_status": "failed",
            }

        suffix = _guess_suffix(filename, mime_type)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(image_bytes)
            temp_path = handle.name

        for extractor in (_extract_with_rapidocr, _extract_with_pytesseract, _extract_with_tesseract_cli):
            ocr_text = normalize_ocr_text(extractor(temp_path))
            if ocr_text:
                ocr_status = "success"
                break

        if not ocr_text and image_bytes:
            ocr_status = "failed"
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    return {
        "filename": filename,
        "mime_type": mime_type,
        "size": max(size, 0),
        "ocr_text": ocr_text,
        "ocr_status": ocr_status,
    }


def extract_texts_from_uploaded_images(uploaded_images: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not isinstance(uploaded_images, list):
        return []

    results: list[dict[str, Any]] = []
    for document in uploaded_images:
        if not isinstance(document, dict):
            continue
        result = extract_text_from_image(document)
        results.append(result)
    return results


def attach_ocr_results_to_uploaded_images(
    uploaded_images: list[dict[str, Any]] | None,
    ocr_results: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    documents = uploaded_images if isinstance(uploaded_images, list) else []
    results = ocr_results if isinstance(ocr_results, list) else []
    attached: list[dict[str, Any]] = []

    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            continue
        merged = dict(document)
        result = results[index] if index < len(results) and isinstance(results[index], dict) else {}
        if result:
            merged["ocr_text"] = normalize_ocr_text(result.get("ocr_text"))
            merged["ocr_status"] = _normalize_text(result.get("ocr_status")) or (
                "success" if merged["ocr_text"] else "failed"
            )
        else:
            merged["ocr_status"] = _normalize_text(document.get("ocr_status")) or "待识别"
            merged["ocr_text"] = normalize_ocr_text(document.get("ocr_text"))
        attached.append(merged)

    return attached


def summarize_ocr_results(ocr_results: list[dict[str, Any]] | None) -> str:
    results = ocr_results if isinstance(ocr_results, list) else []
    if not results:
        return ""

    success = 0
    partial = 0
    failed = 0
    snippets: list[str] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        status = _normalize_text(item.get("ocr_status") or item.get("status")) or "failed"
        text = normalize_ocr_text(item.get("ocr_text") or item.get("text") or item.get("content"))
        if status in {"success", "partial"} and text:
            success += 1
            if status == "partial":
                partial += 1
            snippets.append(text[:32])
        else:
            failed += 1

    parts: list[str] = []
    parts.append(f"OCR识别：{success} 成功 / {partial} 部分 / {failed} 失败")
    if snippets:
        parts.append(f"OCR摘要：{snippets[0]}")
    return "；".join(parts)
