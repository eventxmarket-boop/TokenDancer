from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas.self_fill_assistant import SelfFillAssistantRequest, SelfFillAssistantResponse
from app.services.llm_gateway import LLMGatewayError
from app.services.self_fill_assistant_service import generate_self_fill_assistant_reply

router = APIRouter()


@router.post("/persona-api/self-fill-assistant", response_model=SelfFillAssistantResponse)
async def self_fill_assistant_runtime(
    payload: SelfFillAssistantRequest,
    db: Session = Depends(get_db),
):
    try:
        result = await generate_self_fill_assistant_reply(payload.model_dump(), db=db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMGatewayError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result
