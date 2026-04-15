from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PersonaLoadError(RuntimeError):
    pass


@dataclass(slots=True)
class PersonaPack:
    id: str
    slug: str
    name: str
    category: str
    version: str
    status: str
    avatar: str | None
    tags: list[str]
    topics: list[str]
    intro: str
    profile: str
    mindset: str
    heuristics: str
    expression: str
    persona_examples: str
    state: str
    guardrails: str
    recommended_questions: list[str]
    sort_order: int

    def summary_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "category": self.category,
            "version": self.version,
            "status": self.status,
            "avatar": self.avatar,
            "tags": self.tags,
            "topics": self.topics,
            "intro": self.intro,
            "profile": self.profile,
            "recommendedQuestions": self.recommended_questions,
        }

    def skill_dict(self) -> dict[str, Any]:
        return {
            "meta": {
                "id": self.id,
                "slug": self.slug,
                "name": self.name,
                "category": self.category,
                "version": self.version,
                "status": self.status,
                "avatar": self.avatar,
                "tags": self.tags,
                "topics": self.topics,
                "recommended_questions": self.recommended_questions,
                "sort_order": self.sort_order,
            },
            "intro": self.intro,
            "profile": self.profile,
            "mindset": self.mindset,
            "heuristics": self.heuristics,
            "expression": self.expression,
            "persona_examples": self.persona_examples,
            "state": self.state,
            "guardrails": self.guardrails,
        }


PERSONA_ROOT = Path(__file__).resolve().parents[2] / "personas"


def _read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise PersonaLoadError(f"Missing required file: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PersonaLoadError(f"Invalid JSON in {path}: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise PersonaLoadError(f"Invalid JSON structure in {path}: expected object")

    return data


def _read_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _normalize_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _normalize_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise PersonaLoadError(f"Invalid integer value: {value!r}") from exc


def _iter_persona_dirs() -> list[Path]:
    if not PERSONA_ROOT.exists():
        return []
    return sorted(
        [path for path in PERSONA_ROOT.iterdir() if path.is_dir() and not path.name.startswith(".")],
        key=lambda path: path.name,
    )


def _load_persona_pack(persona_dir: Path) -> PersonaPack:
    meta = _read_json_file(persona_dir / "meta.json")
    required_fields = ["id", "slug", "name", "category", "version", "status"]
    missing = [field for field in required_fields if not str(meta.get(field, "")).strip()]
    if missing:
        raise PersonaLoadError(
            f"Missing required meta fields in {persona_dir.name}: {', '.join(missing)}"
        )

    return PersonaPack(
        id=str(meta["id"]).strip(),
        slug=str(meta["slug"]).strip(),
        name=str(meta["name"]).strip(),
        category=str(meta["category"]).strip(),
        version=str(meta["version"]).strip(),
        status=str(meta["status"]).strip(),
        avatar=str(meta.get("avatar") or "").strip() or None,
        tags=_normalize_str_list(meta.get("tags")),
        topics=_normalize_str_list(meta.get("topics")),
        intro=_read_text_file(persona_dir / "intro.md"),
        profile=_read_text_file(persona_dir / "profile.md"),
        mindset=_read_text_file(persona_dir / "mindset.md"),
        heuristics=_read_text_file(persona_dir / "heuristics.md"),
        expression=_read_text_file(persona_dir / "expression.md"),
        persona_examples=_read_text_file(persona_dir / "persona_examples.md"),
        state=_read_text_file(persona_dir / "state.md"),
        guardrails=_read_text_file(persona_dir / "guardrails.md"),
        recommended_questions=_normalize_str_list(meta.get("recommended_questions")),
        sort_order=_normalize_int(meta.get("sort_order"), default=0),
    )


def _find_persona_dir(slug: str) -> Path | None:
    normalized_slug = slug.strip()
    if not normalized_slug:
        return None

    direct_dir = PERSONA_ROOT / normalized_slug
    if direct_dir.is_dir():
        pack = _load_persona_pack(direct_dir)
        if pack.slug == normalized_slug or pack.id == normalized_slug:
            return direct_dir

    for persona_dir in _iter_persona_dirs():
        meta = _read_json_file(persona_dir / "meta.json")
        if str(meta.get("slug", "")).strip() == normalized_slug or str(meta.get("id", "")).strip() == normalized_slug:
            return persona_dir

    return None


def load_persona_summary(slug: str) -> dict[str, Any] | None:
    persona_dir = _find_persona_dir(slug)
    if persona_dir is None:
        return None
    return _load_persona_pack(persona_dir).summary_dict()


def load_persona_skill(slug: str) -> dict[str, Any] | None:
    persona_dir = _find_persona_dir(slug)
    if persona_dir is None:
        return None
    return _load_persona_pack(persona_dir).skill_dict()


def list_personas() -> list[dict[str, Any]]:
    packs: list[PersonaPack] = []
    for persona_dir in _iter_persona_dirs():
        if not (persona_dir / "meta.json").exists():
            raise PersonaLoadError(f"Missing required file: {persona_dir / 'meta.json'}")
        packs.append(_load_persona_pack(persona_dir))

    packs.sort(key=lambda pack: (pack.sort_order, pack.category, pack.name))
    return [pack.summary_dict() for pack in packs]


def get_persona_by_slug(slug: str) -> dict[str, Any] | None:
    return load_persona_summary(slug)
