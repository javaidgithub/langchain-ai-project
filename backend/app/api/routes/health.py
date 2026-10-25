from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    s = get_settings()
    return {"status": "ok", "version": s.app_version, "environment": s.environment}
