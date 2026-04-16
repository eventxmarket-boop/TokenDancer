from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user, get_optional_current_user

from app.core.version import get_project_version
from app.schemas.created_persona import CreatedPersonaRecord, CreatedPersonaSaveRequest, CreatedPersonaSummary
from app.schemas.create_catalog import CreateCatalogResponse
from app.schemas.create_wizard import CreateWizardDraftRequest, CreateWizardDraftResponse
from app.schemas.persona import PersonaRecord
from app.services.created_persona_service import (
    CreatedPersonaError,
    CreatedPersonaNotFoundError,
    get_created_persona,
    list_created_personas,
    load_created_persona_summary,
    save_created_persona,
)
from app.services.create_catalog_loader import CreateCatalogLoadError, load_create_catalog
from app.services.create_wizard_service import CreateWizardError, build_persona_draft
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


@router.get("/persona-api/create-catalog", response_model=CreateCatalogResponse)
async def create_catalog():
    try:
        return load_create_catalog()
    except CreateCatalogLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/persona-api/create-wizard/draft", response_model=CreateWizardDraftResponse)
async def create_wizard_draft(payload: CreateWizardDraftRequest):
    try:
        draft = build_persona_draft(payload.model_dump())
    except CreateWizardError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"draft": draft}


@router.post("/persona-api/my-seeds", response_model=CreatedPersonaRecord)
async def create_my_seed(
    payload: CreatedPersonaSaveRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        seed = save_created_persona(
            db,
            payload.draft,
            source_type=payload.source_type,
            status=payload.status,
            user_id=current_user.id,
        )
        db.commit()
        return seed
    except CreatedPersonaError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/persona-api/my-seeds/{seed_id}", response_model=CreatedPersonaRecord)
async def update_my_seed(
    seed_id: int,
    payload: CreatedPersonaSaveRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        seed = save_created_persona(
            db,
            payload.draft,
            record_id=seed_id,
            source_type=payload.source_type,
            status=payload.status,
            user_id=current_user.id,
        )
        db.commit()
        return seed
    except CreatedPersonaNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CreatedPersonaError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/persona-api/my-seeds", response_model=list[CreatedPersonaSummary])
async def list_my_seeds(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return list_created_personas(db, user_id=current_user.id)
    except CreatedPersonaError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/persona-api/my-seeds/{seed_id}", response_model=CreatedPersonaRecord)
async def get_my_seed(
    seed_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        seed = get_created_persona(db, seed_id, user_id=current_user.id)
    except CreatedPersonaError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if seed is None:
        raise HTTPException(status_code=404, detail=f"Created seed not found: {seed_id}")

    return seed


@router.get("/persona-api/personas/{slug}", response_model=PersonaRecord)
async def persona_detail(
    slug: str,
    current_user = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    try:
        persona = load_persona_summary(slug)
    except PersonaLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if persona is None:
        try:
            persona = load_created_persona_summary(db, slug, user_id=current_user.id if current_user else None)
        except CreatedPersonaError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    if persona is None:
        raise HTTPException(status_code=404, detail=f"Persona not found: {slug}")

    return persona
