from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/persona-api")
async def persona_root():
    return {
        "service": "tokendancer-persona-station-api",
        "status": "ready",
        "version": "V1.0.0",
    }


@router.get("/persona-api/health")
async def persona_health():
    return {
        "service": "tokendancer-persona-station-api",
        "status": "ok",
        "version": "V1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
