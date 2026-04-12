import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.proxy_errors import ProxyBaseException
from app.deps import (
    ProxyAuthContext,
    ensure_proxy_model_access,
    get_db,
    get_proxy_auth_context,
    rate_limit,
)
from app.schemas.proxy import ChatCompletionRequest, ChatCompletionResponse
from app.services.proxy_gateway_service import proxy_gateway_service

router = APIRouter(tags=["proxy"])
logger = logging.getLogger(__name__)


async def _handle_chat_completion(
    data: ChatCompletionRequest,
    auth: ProxyAuthContext,
    db: Session,
    x_debug_mode: str | None = None,
) -> dict:
    ensure_proxy_model_access(auth, data.model)
    rate_limit(f"proxy:{auth.user_id}:{auth.api_key_id or 'session'}", settings.RATE_LIMIT_PROXY)

    include_debug = settings.DEBUG or auth.user.role == "admin"
    try:
        return await proxy_gateway_service.execute_chat_completion(
            public_model=data.model,
            messages=[message.model_dump() for message in data.messages],
            user_id=auth.user_id,
            user_api_key_id=auth.api_key_id,
            db=db,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            stream=data.stream,
            include_debug=include_debug,
        )
    except ProxyBaseException as exc:
        logger.warning(
            f"[ProxyException] {type(exc).__name__} | user_id={auth.user_id} | {exc.internal_detail}"
        )
        raise exc.to_http()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            f"[Unhandled] Proxy request crashed | user_id={auth.user_id} | {type(exc).__name__}: {exc}",
            exc_info=True,
        )
        detail = "Internal proxy error"
        status_code = 500
        lowered = str(exc).lower()
        if "timeout" in lowered:
            detail = "Upstream request timeout"
            status_code = 504
        elif "connection" in lowered or "refused" in lowered:
            detail = "无法连接上游服务，请稍后重试"
            status_code = 502
        raise HTTPException(status_code=status_code, detail=detail)


@router.post("/proxy/chat/completions", response_model=ChatCompletionResponse)
async def proxy_chat_completions(
    data: ChatCompletionRequest,
    x_debug_mode: str | None = Header(None, alias="X-Debug-Mode"),
    db: Session = Depends(get_db),
    auth: ProxyAuthContext = Depends(get_proxy_auth_context),
):
    return await _handle_chat_completion(data, auth, db, x_debug_mode)


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def openai_compatible_chat_completions(
    data: ChatCompletionRequest,
    x_debug_mode: str | None = Header(None, alias="X-Debug-Mode"),
    db: Session = Depends(get_db),
    auth: ProxyAuthContext = Depends(get_proxy_auth_context),
):
    return await _handle_chat_completion(data, auth, db, x_debug_mode)


@router.get("/v1/models")
def list_models(
    db: Session = Depends(get_db),
    auth: ProxyAuthContext = Depends(get_proxy_auth_context),
):
    rate_limit(f"proxy-models:{auth.user_id}:{auth.api_key_id or 'session'}", settings.RATE_LIMIT_PROXY)
    return {
        "object": "list",
        "data": proxy_gateway_service.list_available_models(db, auth.allowed_models),
    }
