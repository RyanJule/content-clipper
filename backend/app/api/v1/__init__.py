"""API v1 routes"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    accounts,
    auth,
    clips,
    data_deletion,
    health,
    instagram,
    media,
    oauth,
    schedules,
    social,
    tiktok,
    users,
    youtube,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(clips.router, prefix="/clips", tags=["clips"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(social.router, prefix="/social", tags=["social"])
api_router.include_router(instagram.router, prefix="/instagram", tags=["instagram"])
api_router.include_router(youtube.router, prefix="/youtube", tags=["youtube"])
api_router.include_router(tiktok.router, prefix="/tiktok", tags=["tiktok"])
api_router.include_router(data_deletion.router, prefix="/oauth", tags=["data-deletion"])
