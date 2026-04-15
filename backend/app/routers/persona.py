from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.core.version import get_project_version
from app.schemas.persona import PersonaRecord
from app.services.persona_loader import PersonaLoadError, load_persona_summary, list_personas, list_seed_personas

router = APIRouter()


@router.get("/persona-api")
async def persona_root():
    return {
        "service": "tokendancer-persona-station-api",
        "status": "ready",
        "version": get_project_version(),
    }


@router.get("/persona-api/health")
async def persona_health():
    return {
        "service": "tokendancer-persona-station-api",
        "status": "ok",
        "version": get_project_version(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/persona-api/personas", response_model=list[PersonaRecord])
async def persona_list():
    try:
        return list_personas()
    except PersonaLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/persona-api/seed-personas", response_model=list[PersonaRecord])
async def seed_persona_list():
    try:
        return list_seed_personas()
    except PersonaLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/persona-api/personas/{slug}", response_model=PersonaRecord)
async def persona_detail(slug: str):
    try:
        persona = load_persona_summary(slug)
    except PersonaLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if persona is None:
        raise HTTPException(status_code=404, detail=f"Persona not found: {slug}")

    return persona
