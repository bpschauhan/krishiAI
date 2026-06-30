from fastapi import APIRouter

from app.api.routes import auth, geospatial, health, onboarding, version

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(version.router, tags=["version"])
api_router.include_router(onboarding.router, prefix="/api/v1", tags=["onboarding"])
api_router.include_router(auth.router, prefix="/api/v1", tags=["auth"])
api_router.include_router(geospatial.router, prefix="/api/v1", tags=["geospatial"])
