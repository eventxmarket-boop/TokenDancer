from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas.llm_config import (
    LLMConfigDashboardResponse,
    LLMConfigPublic,
    LLMConfigUpsertRequest,
)
from app.services.llm_config_service import (
    LLMConfigServiceError,
    activate_llm_config,
    get_llm_config_dashboard,
    save_llm_config,
    update_llm_config,
)

router = APIRouter()


@router.get("/persona-api/admin/llm-config", response_model=LLMConfigDashboardResponse)
def read_llm_config_dashboard(db: Session = Depends(get_db)):
    try:
        return get_llm_config_dashboard(db)
    except LLMConfigServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/persona-api/admin/llm-config", response_model=LLMConfigPublic)
def create_or_update_llm_config(payload: LLMConfigUpsertRequest, db: Session = Depends(get_db)):
    try:
        return save_llm_config(db, payload)
    except LLMConfigServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/persona-api/admin/llm-config/{config_id}", response_model=LLMConfigPublic)
def replace_llm_config(
    config_id: int,
    payload: LLMConfigUpsertRequest,
    db: Session = Depends(get_db),
):
    try:
        return update_llm_config(db, config_id, payload)
    except LLMConfigServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/persona-api/admin/llm-config/{config_id}/activate", response_model=LLMConfigPublic)
def activate_llm_config_route(config_id: int, db: Session = Depends(get_db)):
    try:
        return activate_llm_config(db, config_id)
    except LLMConfigServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
