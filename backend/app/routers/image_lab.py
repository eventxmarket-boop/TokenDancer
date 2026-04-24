from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from app.schemas.image_lab import (
    ImageGenerateRequest,
    ImageGenerateResponse,
    PlusBridgeSubmitRequest,
    PlusBridgeSubmitResponse,
)
from app.services.openai_image_service import (
    OpenAIImageServiceError,
    generate_image_base64,
)
from app.services.plus_bridge_service import get_latest_plus_bridge_result, store_plus_bridge_result

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/persona-api/image-lab", tags=["image-lab"])


def require_internal_user(request: Request) -> str:
    # TODO: 接入项目真实的内部权限系统；当前仅作为占位校验入口。
    return (request.headers.get("X-Internal-User") or "internal-test-user").strip() or "internal-test-user"


@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image(
    payload: ImageGenerateRequest,
    user_id: str = Depends(require_internal_user),
):
    try:
        result = await run_in_threadpool(
            generate_image_base64,
            payload.prompt,
            payload.size,
            payload.quality,
            payload.output_format,
            user_id=user_id,
        )
        logger.info(
            "image_lab_generate_success user_id=%s prompt_len=%s size=%s quality=%s output_format=%s elapsed_ms=%s",
            user_id,
            len(payload.prompt),
            payload.size,
            payload.quality,
            payload.output_format,
            result.get("elapsed_ms"),
        )
        return ImageGenerateResponse(
            image_base64=result["image_base64"],
            mime_type=result["mime_type"],
            model=result["model"],
            size=result["size"],
            quality=result["quality"],
            output_format=result["output_format"],
        )
    except ValueError as exc:
        logger.warning(
            "image_lab_generate_invalid user_id=%s prompt_len=%s size=%s quality=%s output_format=%s error=%s",
            user_id,
            len(payload.prompt),
            payload.size,
            payload.quality,
            payload.output_format,
            exc,
        )
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OpenAIImageServiceError as exc:
        logger.exception(
            "image_lab_generate_failed user_id=%s prompt_len=%s size=%s quality=%s output_format=%s",
            user_id,
            len(payload.prompt),
            payload.size,
            payload.quality,
            payload.output_format,
        )
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception:
        logger.exception(
            "image_lab_generate_failed user_id=%s prompt_len=%s size=%s quality=%s output_format=%s",
            user_id,
            len(payload.prompt),
            payload.size,
            payload.quality,
            payload.output_format,
        )
        raise HTTPException(status_code=500, detail="图片生成失败，请稍后重试。")


@router.post("/bridge/submit", response_model=PlusBridgeSubmitResponse)
async def submit_plus_bridge_result(
    payload: PlusBridgeSubmitRequest,
    user_id: str = Depends(require_internal_user),
):
    record = store_plus_bridge_result(
        {
            "prompt": payload.prompt,
            "size": payload.size,
            "quality": payload.quality,
            "output_format": payload.output_format,
            "image_base64": payload.image_base64,
            "mime_type": payload.mime_type,
            "model": payload.model,
            "source": payload.source,
            "user_id": payload.user_id or user_id,
        }
    )

    logger.info(
        "image_lab_plus_bridge_submit user_id=%s prompt_len=%s size=%s quality=%s output_format=%s source=%s",
        user_id,
        len(payload.prompt),
        payload.size,
        payload.quality,
        payload.output_format,
        payload.source,
    )

    return PlusBridgeSubmitResponse(**record)


@router.get("/bridge/latest", response_model=PlusBridgeSubmitResponse | None)
async def read_latest_plus_bridge_result():
    record = get_latest_plus_bridge_result()
    if record is None:
        return None
    return PlusBridgeSubmitResponse(**record)
