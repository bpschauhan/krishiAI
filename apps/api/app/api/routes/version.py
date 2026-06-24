from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/version")
def version() -> dict[str, str]:
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
    }
