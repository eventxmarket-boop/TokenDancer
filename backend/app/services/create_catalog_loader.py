from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas.create_catalog import CreateCatalogResponse


class CreateCatalogLoadError(RuntimeError):
    pass


CREATE_CATALOG_ROOT = Path(__file__).resolve().parents[2] / "create_catalog"
CREATE_CATALOG_FILE = CREATE_CATALOG_ROOT / "create_catalog.json"


def _read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CreateCatalogLoadError(f"Missing required file: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CreateCatalogLoadError(f"Invalid JSON in {path}: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise CreateCatalogLoadError(f"Invalid JSON structure in {path}: expected object")

    return data


def load_create_catalog() -> dict[str, Any]:
    data = _read_json_file(CREATE_CATALOG_FILE)
    catalog = CreateCatalogResponse.model_validate(data)
    return catalog.model_dump()
