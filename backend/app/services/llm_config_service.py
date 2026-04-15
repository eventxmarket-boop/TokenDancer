from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.llm_config import LLMConfig
from app.schemas.llm_config import LLMConfigPublic, LLMConfigUpsertRequest

DEFAULT_PROVIDER = "openai_compatible"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 800


class LLMConfigServiceError(RuntimeError):
    pass


@dataclass(slots=True)
class ResolvedLLMConfig:
    provider: str
    base_url: str
    api_key: str
    model_name: str
    temperature: float
    max_tokens: int
    source: str
    config_id: int | None = None


def _env_value(raw: str | None, default: str) -> str:
    value = (raw or "").strip()
    return value or default


def _mask_api_key(api_key: str) -> str:
    cleaned = api_key.strip()
    if not cleaned:
        return ""
    if len(cleaned) <= 8:
        return "********"
    return f"{cleaned[:3]}***{cleaned[-4:]}"


def _normalize_temperature(value: Any, default: float) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise LLMConfigServiceError(f"温度配置无效: {value!r}") from exc


def _normalize_max_tokens(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise LLMConfigServiceError(f"max_tokens 配置无效: {value!r}") from exc


def _normalize_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _serialize(config: LLMConfig) -> LLMConfigPublic:
    return LLMConfigPublic(
        id=config.id,
        provider=config.provider,
        base_url=config.base_url,
        api_key_masked=_mask_api_key(config.api_key),
        model_name=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        is_default=config.is_default,
        is_enabled=config.is_enabled,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def _ordered_configs(db: Session) -> list[LLMConfig]:
    return (
        db.query(LLMConfig)
        .order_by(
            LLMConfig.is_default.desc(),
            LLMConfig.is_enabled.desc(),
            LLMConfig.updated_at.desc(),
            LLMConfig.id.desc(),
        )
        .all()
    )


def list_llm_configs(db: Session) -> list[LLMConfigPublic]:
    return [_serialize(config) for config in _ordered_configs(db)]


def get_current_llm_config(db: Session) -> LLMConfig | None:
    query = (
        db.query(LLMConfig)
        .filter(LLMConfig.is_enabled.is_(True))
        .order_by(
            LLMConfig.is_default.desc(),
            LLMConfig.updated_at.desc(),
            LLMConfig.id.desc(),
        )
    )
    return query.first()


def get_llm_config_dashboard(db: Session) -> dict[str, Any]:
    current = get_current_llm_config(db)
    items = _ordered_configs(db)
    return {
        "current": _serialize(current) if current is not None else None,
        "items": [_serialize(config) for config in items],
    }


def _apply_payload(config: LLMConfig, payload: LLMConfigUpsertRequest) -> LLMConfig:
    config.provider = payload.provider.strip() or DEFAULT_PROVIDER
    config.base_url = payload.base_url.strip() or DEFAULT_BASE_URL
    if payload.api_key is not None:
        cleaned_api_key = payload.api_key.strip()
        if cleaned_api_key or not config.api_key:
            config.api_key = cleaned_api_key
    config.model_name = payload.model_name.strip() or DEFAULT_MODEL
    config.temperature = _normalize_temperature(payload.temperature, config.temperature)
    config.max_tokens = _normalize_max_tokens(payload.max_tokens, config.max_tokens)
    config.is_default = _normalize_bool(payload.is_default, config.is_default)
    config.is_enabled = _normalize_bool(payload.is_enabled, config.is_enabled)
    return config


def _ensure_single_default(db: Session, config_id: int) -> None:
    (
        db.query(LLMConfig)
        .filter(LLMConfig.id != config_id, LLMConfig.is_default.is_(True))
        .update({LLMConfig.is_default: False}, synchronize_session=False)
    )


def save_llm_config(db: Session, payload: LLMConfigUpsertRequest) -> LLMConfigPublic:
    target: LLMConfig | None = None
    if payload.id is not None:
        target = db.query(LLMConfig).filter(LLMConfig.id == payload.id).first()
        if target is None:
            raise LLMConfigServiceError(f"未找到模型配置: {payload.id}")

    if target is None:
        target = LLMConfig()
        db.add(target)

    target = _apply_payload(target, payload)
    db.flush()

    if target.is_default:
        _ensure_single_default(db, target.id)

    db.commit()
    db.refresh(target)
    return _serialize(target)


def update_llm_config(db: Session, config_id: int, payload: LLMConfigUpsertRequest) -> LLMConfigPublic:
    target = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if target is None:
        raise LLMConfigServiceError(f"未找到模型配置: {config_id}")

    target = _apply_payload(target, payload)
    db.flush()

    if target.is_default:
        _ensure_single_default(db, target.id)

    db.commit()
    db.refresh(target)
    return _serialize(target)


def activate_llm_config(db: Session, config_id: int) -> LLMConfigPublic:
    target = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if target is None:
        raise LLMConfigServiceError(f"未找到模型配置: {config_id}")

    (
        db.query(LLMConfig)
        .filter(LLMConfig.id != config_id, LLMConfig.is_default.is_(True))
        .update({LLMConfig.is_default: False}, synchronize_session=False)
    )

    target.is_default = True
    target.is_enabled = True
    db.commit()
    db.refresh(target)
    return _serialize(target)


def _resolve_env_config() -> ResolvedLLMConfig:
    return ResolvedLLMConfig(
        provider=_env_value(getattr(settings, "LLM_PROVIDER", None), DEFAULT_PROVIDER),
        base_url=_env_value(settings.LLM_BASE_URL, DEFAULT_BASE_URL).rstrip("/"),
        api_key=_env_value(settings.LLM_API_KEY, ""),
        model_name=_env_value(settings.LLM_MODEL, DEFAULT_MODEL),
        temperature=_normalize_temperature(settings.LLM_TEMPERATURE, DEFAULT_TEMPERATURE),
        max_tokens=_normalize_max_tokens(settings.LLM_MAX_TOKENS, DEFAULT_MAX_TOKENS),
        source="env",
    )


def resolve_llm_config(db: Session | None = None) -> ResolvedLLMConfig:
    if db is not None:
        current = get_current_llm_config(db)
        if current is not None:
            env_config = _resolve_env_config()
            return ResolvedLLMConfig(
                provider=(current.provider.strip() or env_config.provider),
                base_url=(current.base_url.strip() or env_config.base_url).rstrip("/"),
                api_key=current.api_key.strip() or env_config.api_key,
                model_name=(current.model_name.strip() or env_config.model_name),
                temperature=float(current.temperature if current.temperature is not None else env_config.temperature),
                max_tokens=int(current.max_tokens if current.max_tokens is not None else env_config.max_tokens),
                source="db",
                config_id=current.id,
            )

    env_config = _resolve_env_config()
    if not env_config.api_key.strip():
        raise LLMConfigServiceError("当前模型服务不可用：未配置启用的大模型 API Key")
    return env_config
