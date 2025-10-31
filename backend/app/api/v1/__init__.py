"""API v1 routes"""

from fastapi import APIRouter

from app.api.v1.endpoints import clips, health, media, social, users

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(clips.router, prefix="/clips", tags=["clips"])
api_router.include_router(social.router, prefix="/social", tags=["social"])
