from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas.llm_config import (
    LLMConfigDashboardResponse,
    LLMConfigPublic,
    LLMConfigUpsertRequest,
)
from app.schemas.reply_corpus import (
    ReplyCorpusDashboardResponse,
    ReplyCorpusPublic,
    ReplyCorpusUpsertRequest,
)
from app.services.llm_config_service import (
    LLMConfigServiceError,
    activate_llm_config,
    get_llm_config_dashboard,
    save_llm_config,
    update_llm_config,
)
from app.services.reply_corpus_service import (
    ReplyCorpusServiceError,
    delete_reply_corpus,
    get_reply_corpus_dashboard,
    save_reply_corpus,
    update_reply_corpus,
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


@router.get("/persona-api/admin/reply-corpus", response_model=ReplyCorpusDashboardResponse)
def read_reply_corpus_dashboard(db: Session = Depends(get_db)):
    try:
        return get_reply_corpus_dashboard(db)
    except ReplyCorpusServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/persona-api/admin/reply-corpus", response_model=ReplyCorpusPublic)
def create_or_update_reply_corpus(payload: ReplyCorpusUpsertRequest, db: Session = Depends(get_db)):
    try:
        return save_reply_corpus(db, payload)
    except ReplyCorpusServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/persona-api/admin/reply-corpus/{corpus_id}", response_model=ReplyCorpusPublic)
def replace_reply_corpus(
    corpus_id: int,
    payload: ReplyCorpusUpsertRequest,
    db: Session = Depends(get_db),
):
    try:
        return update_reply_corpus(db, corpus_id, payload)
    except ReplyCorpusServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/persona-api/admin/reply-corpus/{corpus_id}", response_model=ReplyCorpusPublic)
def remove_reply_corpus(corpus_id: int, db: Session = Depends(get_db)):
    try:
        return delete_reply_corpus(db, corpus_id)
    except ReplyCorpusServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
