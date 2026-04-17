from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas.reply_assistant import ReplyAssistantRequest, ReplyAssistantResponse
from app.services.llm_gateway import LLMGatewayError
from app.services.reply_assistant_service import generate_reply_assistant_runtime

router = APIRouter()


@router.post("/persona-api/reply-assistant", response_model=ReplyAssistantResponse)
async def reply_assistant_runtime(
    payload: ReplyAssistantRequest,
    db: Session = Depends(get_db),
):
    try:
        result = await generate_reply_assistant_runtime(payload.model_dump(), db=db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMGatewayError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result
