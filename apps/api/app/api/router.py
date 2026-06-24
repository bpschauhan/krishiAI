from fastapi import APIRouter

from app.api.routes import health, onboarding, version

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(version.router, tags=["version"])
api_router.include_router(onboarding.router, prefix="/api/v1", tags=["onboarding"])
