"""
TikTok Content Posting API Endpoints

Provides endpoints for:
- Account/creator info
- Video upload and publishing
- Photo post publishing
- Stories publishing
- Publish status tracking
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.core.crypto import decrypt_token
from app.models.account import Account
from app.models.user import User
from app.services.oauth_service import refresh_account_token
from app.services.tiktok_service import (
    TikTokAPIError,
    TikTokAuthError,
    TikTokService,
    create_tiktok_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Request/Response Schemas ====================

class VideoPublishByUrlRequest(BaseModel):
    video_url: str
    title: str = ""
    privacy_level: str = "SELF_ONLY"
    disable_duet: bool = False
    disable_comment: bool = False
    disable_stitch: bool = False
    video_cover_timestamp_ms: int = 0


class PhotoPostRequest(BaseModel):
    photo_urls: List[str]
    title: str = ""
    privacy_level: str = "SELF_ONLY"
    disable_comment: bool = False
    auto_add_music: bool = True


class StoryPublishRequest(BaseModel):
    media_url: str
    media_type: str = "VIDEO"  # VIDEO or PHOTO


class PublishStatusRequest(BaseModel):
    publish_id: str


# ==================== Helpers ====================

async def _get_tiktok_service(
    current_user: User,
    db: Session,
) -> TikTokService:
    """Get an authenticated TikTok service for the current user.

    Proactively refreshes the access token when it is expired or within
    5 minutes of expiry. TikTok access tokens last 24 hours; refresh tokens
    last 365 days.
    """
    account = (
        db.query(Account)
        .filter(
            Account.user_id == current_user.id,
            Account.platform == "tiktok",
            Account.is_active == True,
        )
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active TikTok account found. Please connect your TikTok account first.",
        )

    # Proactively refresh if the access token is expired or expiring within 5 minutes
    if account.token_expires_at:
        now = datetime.utcnow()
        if now + timedelta(minutes=5) >= account.token_expires_at:
            logger.info(
                f"TikTok access token for account {account.id} is expiring soon; refreshing."
            )
            try:
                account = await refresh_account_token(db, account)
            except Exception as e:
                logger.error(
                    f"Failed to refresh TikTok token for account {account.id}: {e}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="TikTok access token has expired and could not be refreshed. Please reconnect your account.",
                )

    access_token = decrypt_token(account.access_token_enc)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TikTok access token is invalid. Please reconnect your account.",
        )

    return create_tiktok_service(access_token)


# ==================== Account/Creator Info ====================

@router.get("/account")
async def get_account_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated user's TikTok account information."""
    tt = await _get_tiktok_service(current_user, db)
    try:
        user_info = await tt.get_user_info()
        return user_info
    except TikTokAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except TikTokAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await tt.close()


@router.get("/creator-info")
async def get_creator_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get creator info including posting constraints.

    Returns privacy level options, max video duration, and other creator-specific settings.
    """
    tt = await _get_tiktok_service(current_user, db)
    try:
        creator_info = await tt.query_creator_info()
        return creator_info
    except TikTokAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except TikTokAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await tt.close()


# ==================== Video Publishing ====================

@router.post("/publish/video/url")
async def publish_video_by_url(
    request: VideoPublishByUrlRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Directly publish a video to TikTok from a publicly accessible URL.

    TikTok will pull the video from the provided URL and publish it directly
    to the creator's feed using the video.publish scope (DIRECT_POST mode).
    Use /publish/status to track publishing progress.
    """
    tt = await _get_tiktok_service(current_user, db)
    try:
        result = await tt.publish_video_by_url(
            video_url=request.video_url,
            title=request.title,
            privacy_level=request.privacy_level,
            disable_duet=request.disable_duet,
            disable_comment=request.disable_comment,
            disable_stitch=request.disable_stitch,
            video_cover_timestamp_ms=request.video_cover_timestamp_ms,
        )
        return {
            "success": True,
            "publish_id": result["publish_id"],
            "message": "Video is being published to TikTok. Use /publish/status to track progress.",
        }
    except TikTokAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except TikTokAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await tt.close()


@router.post("/upload/video")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(""),
    privacy_level: str = Form("SELF_ONLY"),
    disable_duet: bool = Form(False),
    disable_comment: bool = Form(False),
    disable_stitch: bool = Form(False),
    video_cover_timestamp_ms: int = Form(0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload a video file and directly publish it to TikTok.

    Accepts multipart form data with the video file. The video is uploaded
    to TikTok and published directly to the creator's feed using the
    video.publish scope (DIRECT_POST mode). Use /publish/status to track progress.

    Uses streaming upload when file.size is available (FastAPI 0.103+) to
    avoid loading the entire video into memory, preventing OOM crashes on
    large uploads that would otherwise cause a 502 from the proxy layer.
    """
    tt = await _get_tiktok_service(current_user, db)
    try:
        common_kwargs = dict(
            title=title,
            privacy_level=privacy_level,
            disable_duet=disable_duet,
            disable_comment=disable_comment,
            disable_stitch=disable_stitch,
            video_cover_timestamp_ms=video_cover_timestamp_ms,
        )

        video_size = file.size

        if video_size is not None:
            # Streaming path: never loads more than one chunk at a time.
            # file.size is populated by FastAPI's multipart parser (0.103+).
            if video_size == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Video file is empty.",
                )
            result = await tt.upload_video_stream(
                file=file,
                video_size=video_size,
                **common_kwargs,
            )
        else:
            # Fallback for clients that don't report Content-Length on the part.
            video_data = await file.read()
            result = await tt.upload_video_bytes(
                video_data=video_data,
                **common_kwargs,
            )

        return {
            "success": True,
            "publish_id": result["publish_id"],
            "message": "Video is being published to TikTok. Use /publish/status to track progress.",
        }

    except TikTokAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except TikTokAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.error(f"TikTok video upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )
    finally:
        await tt.close()


# ==================== Photo Post Publishing ====================

@router.post("/publish/photo")
async def publish_photo_post(
    request: PhotoPostRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Publish a photo post (carousel of images) to TikTok.

    Supports 1-35 images via publicly accessible URLs.
    Use /publish/status to track the publishing progress.
    """
    tt = await _get_tiktok_service(current_user, db)
    try:
        result = await tt.publish_photo_post(
            photo_urls=request.photo_urls,
            title=request.title,
            privacy_level=request.privacy_level,
            disable_comment=request.disable_comment,
            auto_add_music=request.auto_add_music,
        )
        return {
            "success": True,
            "publish_id": result["publish_id"],
            "message": "Photo post initiated. Use /publish/status to check progress.",
        }
    except TikTokAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except TikTokAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await tt.close()


# ==================== Stories Publishing ====================

@router.post("/publish/story/url")
async def publish_story_by_url(
    request: StoryPublishRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Publish a story from a publicly accessible URL.

    Stories are visible for 24 hours.
    Supports both video and photo stories.
    """
    tt = await _get_tiktok_service(current_user, db)
    try:
        result = await tt.publish_story_by_url(
            media_url=request.media_url,
            media_type=request.media_type,
        )
        return {
            "success": True,
            "publish_id": result["publish_id"],
            "message": "Story sent to your TikTok inbox. Open TikTok to finalize and publish.",
        }
    except TikTokAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except TikTokAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await tt.close()


@router.post("/upload/story")
async def upload_story_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload a video story to the user's TikTok inbox.

    Accepts multipart form data with the video file. The video is uploaded
    to TikTok and placed in the user's inbox for finalization.
    """
    tt = await _get_tiktok_service(current_user, db)
    try:
        video_data = await file.read()

        result = await tt.upload_story_video_bytes(
            video_data=video_data,
        )

        return {
            "success": True,
            "publish_id": result["publish_id"],
            "message": "Story video uploaded to your TikTok inbox. Open TikTok to finalize and publish.",
        }

    except TikTokAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except TikTokAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.error(f"TikTok story upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Story upload failed: {str(e)}",
        )
    finally:
        await tt.close()


# ==================== Publish Status ====================

@router.post("/publish/status")
async def get_publish_status(
    request: PublishStatusRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Check the status of a publish operation.

    Returns status: PROCESSING_UPLOAD, PROCESSING_DOWNLOAD,
    SEND_TO_USER_INBOX, PUBLISH_COMPLETE, or FAILED.
    """
    tt = await _get_tiktok_service(current_user, db)
    try:
        status_data = await tt.get_publish_status(request.publish_id)
        return status_data
    except TikTokAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except TikTokAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await tt.close()
