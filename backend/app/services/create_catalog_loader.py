from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas.create_catalog import CreateCatalogResponse


class CreateCatalogLoadError(RuntimeError):
    pass


CREATE_CATALOG_ROOT = Path(__file__).resolve().parents[2] / "create_catalog"
CREATE_CATALOG_FILE = CREATE_CATALOG_ROOT / "create_catalog.json"
INTIMATE_CANONICAL_SLUG = "relationship_management"
INTIMATE_CANONICAL_SOURCE_REPOS = {
    "relationship-training-skill",
    "xinyi",
    "partner-skill",
    "npy-skill",
}
INTIMATE_CANONICAL_SOURCE_URLS = {
    "https://github.com/TammyTan516/relationship-training-skill",
    "https://github.com/kroxchan/xinyi",
    "https://github.com/NatalieCao323/partner-skill",
    "https://github.com/wwwttlll/npy-skill",
}
REPLY_ASSISTANT_CANONICAL_SLUG = "reply_assistant"
REPLY_ASSISTANT_CANONICAL_SOURCE_REPOS = {
    "relationship-training-skill",
    "xinyi",
    "partner-skill",
    "npy-skill",
    "crush-skill",
    "ex-skill",
    "colleague-skill",
    "teammate-skill",
}
REPLY_ASSISTANT_CANONICAL_SOURCE_URLS = {
    "https://github.com/TammyTan516/relationship-training-skill",
    "https://github.com/kroxchan/xinyi",
    "https://github.com/NatalieCao323/partner-skill",
    "https://github.com/wwwttlll/npy-skill",
    "https://github.com/yyyyyyylll/crush-skill",
    "https://github.com/titanwings/ex-skill",
    "https://github.com/titanwings/colleague-skill",
    "https://github.com/LeoYeAI/teammate-skill",
}


def _normalize_intimate_slug(value: str) -> str:
    if value in {
        "relationship_understanding",
        "relationship_maintenance",
        "partner_maintenance",
    }:
        return INTIMATE_CANONICAL_SLUG
    return value


def _normalize_intimate_item(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("create_type") != "intimate_companion":
        return item

    normalized_slug = _normalize_intimate_slug(str(item.get("slug") or "").strip())
    source_repos = [
        str(value).strip()
        for value in [item.get("source_repo"), *(item.get("source_repos") or [])]
        if str(value).strip()
    ]
    source_urls = [
        str(value).strip()
        for value in [item.get("repo_url"), *(item.get("source_urls") or [])]
        if str(value).strip()
    ]
    canonical_source_repo = next((repo for repo in source_repos if repo in INTIMATE_CANONICAL_SOURCE_REPOS), None)
    canonical_source_url = next((url for url in source_urls if url in INTIMATE_CANONICAL_SOURCE_URLS), None)
    fallback_source_repo = item.get("source_repo") or (source_repos[0] if source_repos else "")
    fallback_source_url = item.get("repo_url") or (source_urls[0] if source_urls else "")

    return {
        **item,
        "slug": normalized_slug,
        "name": "关系经营" if normalized_slug == INTIMATE_CANONICAL_SLUG else item.get("name", ""),
        "source_repo": canonical_source_repo or fallback_source_repo,
        "repo_url": canonical_source_url or fallback_source_url,
        "source_repos": source_repos,
        "source_urls": source_urls,
    }


def _normalize_reply_assistant_slug(value: str) -> str:
    if value in {"message_simulation", "crush"}:
        return REPLY_ASSISTANT_CANONICAL_SLUG
    return value


def _normalize_reply_assistant_item(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("create_type") != "reply_assistant":
        return item

    normalized_slug = _normalize_reply_assistant_slug(str(item.get("slug") or "").strip())
    source_repos = [
        str(value).strip()
        for value in [item.get("source_repo"), *(item.get("source_repos") or [])]
        if str(value).strip()
    ]
    source_urls = [
        str(value).strip()
        for value in [item.get("repo_url"), *(item.get("source_urls") or [])]
        if str(value).strip()
    ]
    canonical_source_repo = next((repo for repo in source_repos if repo in REPLY_ASSISTANT_CANONICAL_SOURCE_REPOS), None)
    canonical_source_url = next((url for url in source_urls if url in REPLY_ASSISTANT_CANONICAL_SOURCE_URLS), None)
    fallback_source_repo = item.get("source_repo") or (source_repos[0] if source_repos else "")
    fallback_source_url = item.get("repo_url") or (source_urls[0] if source_urls else "")

    return {
        **item,
        "slug": normalized_slug,
        "name": "我该怎么回" if normalized_slug == REPLY_ASSISTANT_CANONICAL_SLUG else item.get("name", ""),
        "source_repo": canonical_source_repo or fallback_source_repo,
        "repo_url": canonical_source_url or fallback_source_url,
        "source_repos": source_repos,
        "source_urls": source_urls,
    }


def _normalize_create_catalog_group(group: dict[str, Any]) -> dict[str, Any]:
    group_name = group.get("group")
    if group_name not in {"relationship_intimate", "reply_assistant"}:
        return group

    item_normalizer = _normalize_reply_assistant_item if group_name == "reply_assistant" else _normalize_intimate_item
    slug_normalizer = _normalize_reply_assistant_slug if group_name == "reply_assistant" else _normalize_intimate_slug
    canonical_slug = REPLY_ASSISTANT_CANONICAL_SLUG if group_name == "reply_assistant" else INTIMATE_CANONICAL_SLUG
    canonical_name = "我该怎么回" if group_name == "reply_assistant" else "关系经营"

    ordered_items = sorted(
        (item_normalizer(item) for item in group.get("items", []) if isinstance(item, dict)),
        key=lambda item: int(item.get("sort_order") or 0),
    )
    deduped: dict[str, dict[str, Any]] = {}
    for item in ordered_items:
        slug = slug_normalizer(str(item.get("slug") or "").strip())
        existing = deduped.get(slug)
        if existing is None:
            deduped[slug] = {
                **item,
                "slug": slug,
                "name": canonical_name if slug == canonical_slug else item.get("name", ""),
            }
            continue

        merged_source_repos = []
        merged_source_urls = []
        for value in [existing.get("source_repo"), *(existing.get("source_repos") or []), item.get("source_repo"), *(item.get("source_repos") or [])]:
            text = str(value).strip()
            if text and text not in merged_source_repos:
                merged_source_repos.append(text)
        for value in [existing.get("repo_url"), *(existing.get("source_urls") or []), item.get("repo_url"), *(item.get("source_urls") or [])]:
            text = str(value).strip()
            if text and text not in merged_source_urls:
                merged_source_urls.append(text)
        deduped[slug] = {
            **existing,
            **item,
            "slug": slug,
            "name": canonical_name if slug == canonical_slug else existing.get("name", ""),
            "source_repo": merged_source_repos[0] if merged_source_repos else existing.get("source_repo", ""),
            "repo_url": merged_source_urls[0] if merged_source_urls else existing.get("repo_url", ""),
            "source_repos": merged_source_repos,
            "source_urls": merged_source_urls,
            "description": existing.get("description") or item.get("description") or "",
        }

    group_items = sorted(deduped.values(), key=lambda item: int(item.get("sort_order") or 0))
    return {
        **group,
        "items": group_items,
    }


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
    payload = catalog.model_dump()
    payload["groups"] = [_normalize_create_catalog_group(group) for group in payload.get("groups", [])]
    return payload
