from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.schemas.style_profile import StyleProfileDraft, StyleProfileDimensions, StyleProfileSelection


class StyleProfileError(RuntimeError):
    pass


DATA_DIR = Path(__file__).resolve().parents[1] / "data"

_DIMENSIONS = ("depth", "humor", "directness", "warmth", "pace", "structure", "boundary")

_DIMENSION_LABELS = {
    "depth": ("浅", "中等", "深"),
    "humor": ("克制", "适中", "灵动"),
    "directness": ("婉转", "平衡", "直接"),
    "warmth": ("冷静", "温和", "温暖"),
    "pace": ("慢", "平衡", "快"),
    "structure": ("松散", "平衡", "结构清晰"),
    "boundary": ("柔和", "平衡", "边界感强"),
}

_MBTI_ALIASES = {
    "INTJ-A": "INTJ",
    "INTJ-T": "INTJ",
    "INTP-A": "INTP",
    "INTP-T": "INTP",
    "ENTJ-A": "ENTJ",
    "ENTJ-T": "ENTJ",
    "ENTP-A": "ENTP",
    "ENTP-T": "ENTP",
    "INFJ-A": "INFJ",
    "INFJ-T": "INFJ",
    "INFP-A": "INFP",
    "INFP-T": "INFP",
    "ENFJ-A": "ENFJ",
    "ENFJ-T": "ENFJ",
    "ENFP-A": "ENFP",
    "ENFP-T": "ENFP",
    "ISTJ-A": "ISTJ",
    "ISTJ-T": "ISTJ",
    "ISFJ-A": "ISFJ",
    "ISFJ-T": "ISFJ",
    "ESTJ-A": "ESTJ",
    "ESTJ-T": "ESTJ",
    "ESFJ-A": "ESFJ",
    "ESFJ-T": "ESFJ",
    "ISTP-A": "ISTP",
    "ISTP-T": "ISTP",
    "ISFP-A": "ISFP",
    "ISFP-T": "ISFP",
    "ESTP-A": "ESTP",
    "ESTP-T": "ESTP",
    "ESFP-A": "ESFP",
    "ESFP-T": "ESFP",
}

_ZODIAC_ALIASES = {
    "白羊": "Aries",
    "金牛": "Taurus",
    "双子": "Gemini",
    "巨蟹": "Cancer",
    "狮子": "Leo",
    "处女": "Virgo",
    "天秤": "Libra",
    "天蝎": "Scorpio",
    "射手": "Sagittarius",
    "摩羯": "Capricorn",
    "水瓶": "Aquarius",
    "双鱼": "Pisces",
}

_MBTI_DIMENSION_WEIGHTS = {
    "depth": 0.58,
    "humor": 0.34,
    "directness": 0.68,
    "warmth": 0.34,
    "pace": 0.58,
    "structure": 0.78,
    "boundary": 0.58,
}

_ZODIAC_DIMENSION_WEIGHTS = {
    "depth": 0.45,
    "humor": 0.54,
    "directness": 0.32,
    "warmth": 0.64,
    "pace": 0.42,
    "structure": 0.38,
    "boundary": 0.46,
}

_DEFAULT_DIMENSION_BIAS = {
    "depth": 0.0,
    "humor": 0.0,
    "directness": 0.0,
    "warmth": 0.0,
    "pace": 0.0,
    "structure": 0.0,
    "boundary": 0.0,
}


@lru_cache(maxsize=1)
def _load_traits(filename: str) -> dict[str, Any]:
    path = DATA_DIR / filename
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StyleProfileError(f"Invalid JSON in {path}: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise StyleProfileError(f"Invalid JSON structure in {path}: expected object")
    return payload


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_mbti_type(value: Any) -> str:
    text = _normalize_text(value).upper().replace(" ", "")
    if not text:
        return ""
    text = _MBTI_ALIASES.get(text, text)
    if text in _load_traits("mbti_traits.json"):
        return text
    if len(text) >= 4:
        candidate = text[:4]
        if candidate in _load_traits("mbti_traits.json"):
            return candidate
    return ""


def normalize_zodiac_sign(value: Any) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    lower = text.lower()
    for key in _load_traits("zodiac_traits.json"):
        if lower == key.lower():
            return key
    alias = _ZODIAC_ALIASES.get(text)
    if alias:
        return alias
    return ""


def _pick_selection(form_data: dict[str, Any]) -> StyleProfileSelection:
    mbti_type = normalize_mbti_type(
        form_data.get("style_mbti_type")
        or form_data.get("mbti_type")
        or form_data.get("mbti")
        or form_data.get("mbtiTag")
    )
    zodiac_sign = normalize_zodiac_sign(
        form_data.get("style_zodiac_sign")
        or form_data.get("zodiac_sign")
        or form_data.get("zodiac")
        or form_data.get("zodiacSign")
    )
    return StyleProfileSelection(mbti_type=mbti_type, zodiac_sign=zodiac_sign)


def _trait_bias(trait: dict[str, Any], dimension: str) -> float:
    bias = trait.get("bias") or {}
    if not isinstance(bias, dict):
        return 0.0
    value = bias.get(dimension, 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _dimension_label(dimension: str, score: float) -> str:
    low, mid, high = _DIMENSION_LABELS[dimension]
    if score <= -0.35:
        return low
    if score >= 0.35:
        return high
    return mid


def _decision_style_label(mbti_trait: dict[str, Any] | None, zodiac_trait: dict[str, Any] | None) -> str:
    if mbti_trait:
        label = _normalize_text(mbti_trait.get("decision_style"))
        if label:
            return label
    if zodiac_trait:
        label = _normalize_text(zodiac_trait.get("decision_style"))
        if label:
            return label
    return "平衡型"


def _build_dimension_score(
    dimension: str,
    mbti_trait: dict[str, Any] | None,
    zodiac_trait: dict[str, Any] | None,
) -> float:
    numerator = 0.0
    denominator = 0.0

    if mbti_trait:
        weight = _MBTI_DIMENSION_WEIGHTS.get(dimension, 0.5)
        numerator += _trait_bias(mbti_trait, dimension) * weight
        denominator += weight

    if zodiac_trait:
        weight = _ZODIAC_DIMENSION_WEIGHTS.get(dimension, 0.5)
        numerator += _trait_bias(zodiac_trait, dimension) * weight
        denominator += weight

    if denominator <= 0:
        return 0.0
    return max(-1.0, min(1.0, numerator / denominator))


def _build_dimension_points(
    dimensions: StyleProfileDimensions,
    mbti_trait: dict[str, Any] | None,
    zodiac_trait: dict[str, Any] | None,
) -> list[str]:
    points = [
        f"depth：{dimensions.depth}",
        f"humor：{dimensions.humor}",
        f"directness：{dimensions.directness}",
        f"warmth：{dimensions.warmth}",
        f"pace：{dimensions.pace}",
        f"structure：{dimensions.structure}",
        f"boundary：{dimensions.boundary}",
        f"decision_style：{dimensions.decision_style}",
    ]

    if mbti_trait:
        mbti_name = _normalize_text(mbti_trait.get("name")) or _normalize_text(mbti_trait.get("type"))
        summary = _normalize_text(mbti_trait.get("summary"))
        if mbti_name:
            points.insert(0, f"MBTI：{mbti_name}")
        if summary:
            points.append(f"MBTI 提示：{summary}")

    if zodiac_trait:
        zodiac_name = _normalize_text(zodiac_trait.get("name")) or _normalize_text(zodiac_trait.get("type"))
        summary = _normalize_text(zodiac_trait.get("summary"))
        if zodiac_name:
            points.insert(1 if mbti_trait else 0, f"星座：{zodiac_name}")
        if summary:
            points.append(f"星座 提示：{summary}")

    return points


def build_style_profile(form_data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(form_data, dict):
        raise StyleProfileError("form_data must be an object")

    selection = _pick_selection(form_data)
    mbti_traits = _load_traits("mbti_traits.json")
    zodiac_traits = _load_traits("zodiac_traits.json")
    mbti_trait = mbti_traits.get(selection.mbti_type) if selection.mbti_type else None
    zodiac_trait = zodiac_traits.get(selection.zodiac_sign) if selection.zodiac_sign else None

    if not mbti_trait and not zodiac_trait:
        return StyleProfileDraft(selection=selection).model_dump()

    depth = _dimension_label("depth", _build_dimension_score("depth", mbti_trait, zodiac_trait))
    humor = _dimension_label("humor", _build_dimension_score("humor", mbti_trait, zodiac_trait))
    directness = _dimension_label("directness", _build_dimension_score("directness", mbti_trait, zodiac_trait))
    warmth = _dimension_label("warmth", _build_dimension_score("warmth", mbti_trait, zodiac_trait))
    pace = _dimension_label("pace", _build_dimension_score("pace", mbti_trait, zodiac_trait))
    structure = _dimension_label("structure", _build_dimension_score("structure", mbti_trait, zodiac_trait))
    boundary = _dimension_label("boundary", _build_dimension_score("boundary", mbti_trait, zodiac_trait))
    decision_style = _decision_style_label(mbti_trait, zodiac_trait)

    dimensions = StyleProfileDimensions(
        depth=depth,
        humor=humor,
        directness=directness,
        warmth=warmth,
        pace=pace,
        structure=structure,
        boundary=boundary,
        decision_style=decision_style,
    )

    conflict_notes: list[str] = []
    if selection.mbti_type and selection.zodiac_sign:
        conflict_notes.append("MBTI 负责结构、决策和节奏；星座负责温度、边界和轻快感，已收敛为一套回答气质。")

    summary_bits = []
    if selection.mbti_type:
        summary_bits.append(_normalize_text(mbti_trait.get("summary")) if mbti_trait else "")
    if selection.zodiac_sign:
        summary_bits.append(_normalize_text(zodiac_trait.get("summary")) if zodiac_trait else "")
    summary_bits = [bit for bit in summary_bits if bit]
    summary = ""
    if summary_bits:
        summary = " / ".join(summary_bits[:2])
    if not summary:
        summary = "回答气质已完成轻量调音。"

    points = _build_dimension_points(dimensions, mbti_trait, zodiac_trait)
    if conflict_notes:
        points.extend(conflict_notes)

    return StyleProfileDraft(
        selection=selection,
        summary=summary,
        points=points,
        dimensions=dimensions,
        mbti_traits=_split_trait_notes(mbti_trait),
        zodiac_traits=_split_trait_notes(zodiac_trait),
        conflict_notes=conflict_notes,
    ).model_dump()


def _split_trait_notes(trait: dict[str, Any] | None) -> list[str]:
    if not trait:
        return []
    notes: list[str] = []
    for key in ("traits", "notes", "keywords"):
        raw = trait.get(key)
        if isinstance(raw, list):
            notes.extend(_normalize_text(item) for item in raw if _normalize_text(item))
        elif isinstance(raw, str):
            notes.extend(line.strip("•- \t") for line in raw.splitlines() if line.strip())
    return [note for note in notes if note]
