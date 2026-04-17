from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas.how_to_do import HowToDoRequest, HowToDoResponse
from app.services.how_to_do_service import generate_how_to_do_runtime

router = APIRouter()


@router.post("/persona-api/how-to-do", response_model=HowToDoResponse)
async def persona_how_to_do(
    payload: HowToDoRequest,
    db: Session = Depends(get_db),
):
    try:
        return await generate_how_to_do_runtime(payload.model_dump(), db=db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
