from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionClearResponse
from app.services.chat_service import (
    ChatServiceError,
    PersonaNotFoundError,
    chat_with_persona,
    clear_chat_session,
)
from app.services.llm_gateway import LLMGatewayError
from app.services.persona_loader import PersonaLoadError

router = APIRouter()


@router.post("/persona-api/chat", response_model=ChatResponse)
async def persona_chat(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        return await chat_with_persona(
            persona_slug=payload.persona_slug,
            session_id=payload.session_id,
            user_message=payload.message,
            db=db,
        )
    except PersonaNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersonaLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except LLMGatewayError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ChatServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/persona-api/sessions/{session_id}/clear", response_model=ChatSessionClearResponse)
def persona_chat_clear(session_id: str, db: Session = Depends(get_db)):
    try:
        clear_chat_session(db, session_id)
    except ChatServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChatSessionClearResponse(session_id=session_id)
