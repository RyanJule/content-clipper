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
    brand_content_toggle: bool = False
    brand_organic_toggle: bool = False


class PhotoPostRequest(BaseModel):
    photo_urls: List[str]
    title: str = ""
    privacy_level: str = "SELF_ONLY"
    disable_comment: bool = False
    auto_add_music: bool = True
    brand_content_toggle: bool = False
    brand_organic_toggle: bool = False


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


async def _validate_with_creator_info(
    tt: TikTokService,
    privacy_level: str,
    disable_duet: bool,
    disable_comment: bool,
    disable_stitch: bool,
    brand_content_toggle: bool = False,
) -> tuple[str, bool, bool, bool]:
    """Call TikTok's creator_info/query/ and enforce posting constraints.

    TikTok requires this call before every post init (it is their mechanism for
    verifying that the integration follows Content Sharing Guidelines).  Skipping
    it causes a 403 "Please review our integration guidelines" on the subsequent
    video/init or content/init call.

    Validates the requested privacy_level against the allowed options and enforces
    any creator-level interaction locks (duet_disabled, comment_disabled,
    stitch_disabled) returned by TikTok.

    Also enforces TikTok's guideline that branded content (brand_content_toggle=True)
    cannot be set to SELF_ONLY privacy — doing so triggers a 403 from TikTok.

    Returns the (potentially corrected) tuple of posting constraints.
    """
    creator_info = await tt.query_creator_info()

    # Validate privacy level against creator-allowed options
    allowed_privacy = creator_info.get("privacy_level_options", [])
    if allowed_privacy and privacy_level not in allowed_privacy:
        # Fall back to the first allowed option rather than failing with a
        # confusing error; the endpoint still surfaces the issue via logging.
        logger.warning(
            f"Requested privacy_level '{privacy_level}' is not in creator's allowed "
            f"options {allowed_privacy}. Falling back to '{allowed_privacy[0]}'."
        )
        privacy_level = allowed_privacy[0]

    # TikTok's Content Sharing Guidelines forbid combining brand_content_toggle=True
    # with SELF_ONLY privacy. This combination triggers a 403 "integration guidelines"
    # error from TikTok's API even when creator_info/query/ was called correctly.
    if brand_content_toggle and privacy_level == "SELF_ONLY":
        non_private = next(
            (opt for opt in (allowed_privacy or []) if opt != "SELF_ONLY"),
            "PUBLIC_TO_EVERYONE",
        )
        logger.warning(
            f"brand_content_toggle=True is incompatible with SELF_ONLY privacy. "
            f"Overriding to '{non_private}'."
        )
        privacy_level = non_private

    # Enforce creator-level interaction locks
    if creator_info.get("duet_disabled"):
        disable_duet = True
    if creator_info.get("comment_disabled"):
        disable_comment = True
    if creator_info.get("stitch_disabled"):
        disable_stitch = True

    return privacy_level, disable_duet, disable_comment, disable_stitch


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
        # TikTok 4xx = policy/client error → 422; TikTok 5xx or unknown → 502
        http_status = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if e.upstream_status is not None and 400 <= e.upstream_status < 500
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=http_status, detail=str(e))
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
        # TikTok 4xx = policy/client error → 422; TikTok 5xx or unknown → 502
        http_status = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if e.upstream_status is not None and 400 <= e.upstream_status < 500
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=http_status, detail=str(e))
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
        # TikTok requires creator_info/query/ before every post init.
        privacy_level, disable_duet, disable_comment, disable_stitch = (
            await _validate_with_creator_info(
                tt,
                request.privacy_level,
                request.disable_duet,
                request.disable_comment,
                request.disable_stitch,
                brand_content_toggle=request.brand_content_toggle,
            )
        )
        result = await tt.publish_video_by_url(
            video_url=request.video_url,
            title=request.title,
            privacy_level=privacy_level,
            disable_duet=disable_duet,
            disable_comment=disable_comment,
            disable_stitch=disable_stitch,
            video_cover_timestamp_ms=request.video_cover_timestamp_ms,
            brand_content_toggle=request.brand_content_toggle,
            brand_organic_toggle=request.brand_organic_toggle,
        )
        return {
            "success": True,
            "publish_id": result["publish_id"],
            "message": "Video is being published to TikTok. Use /publish/status to track progress.",
        }
    except TikTokAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except TikTokAPIError as e:
        # TikTok 4xx = policy/client error → 422; TikTok 5xx or unknown → 502
        http_status = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if e.upstream_status is not None and 400 <= e.upstream_status < 500
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=http_status, detail=str(e))
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
    brand_content_toggle: bool = Form(False),
    brand_organic_toggle: bool = Form(False),
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
        # TikTok requires creator_info/query/ to be called before every post
        # init so it can verify Content Sharing Guidelines compliance.  Skipping
        # it returns 403 "Please review our integration guidelines".
        privacy_level, disable_duet, disable_comment, disable_stitch = (
            await _validate_with_creator_info(
                tt,
                privacy_level,
                disable_duet,
                disable_comment,
                disable_stitch,
                brand_content_toggle=brand_content_toggle,
            )
        )

        common_kwargs = dict(
            title=title,
            privacy_level=privacy_level,
            disable_duet=disable_duet,
            disable_comment=disable_comment,
            disable_stitch=disable_stitch,
            video_cover_timestamp_ms=video_cover_timestamp_ms,
            brand_content_toggle=brand_content_toggle,
            brand_organic_toggle=brand_organic_toggle,
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
        # TikTok 4xx = policy/client error → 422; TikTok 5xx or unknown → 502
        http_status = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if e.upstream_status is not None and 400 <= e.upstream_status < 500
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=http_status, detail=str(e))
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
        # TikTok requires creator_info/query/ before every post init.
        # Photo posts only use privacy_level and disable_comment from creator info.
        privacy_level, _, disable_comment, _ = (
            await _validate_with_creator_info(
                tt,
                request.privacy_level,
                False,
                request.disable_comment,
                False,
            )
        )
        result = await tt.publish_photo_post(
            photo_urls=request.photo_urls,
            title=request.title,
            privacy_level=privacy_level,
            disable_comment=disable_comment,
            auto_add_music=request.auto_add_music,
            brand_content_toggle=request.brand_content_toggle,
            brand_organic_toggle=request.brand_organic_toggle,
        )
        return {
            "success": True,
            "publish_id": result["publish_id"],
            "message": "Photo post initiated. Use /publish/status to check progress.",
        }
    except TikTokAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except TikTokAPIError as e:
        # TikTok 4xx = policy/client error → 422; TikTok 5xx or unknown → 502
        http_status = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if e.upstream_status is not None and 400 <= e.upstream_status < 500
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=http_status, detail=str(e))
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
        # TikTok 4xx = policy/client error → 422; TikTok 5xx or unknown → 502
        http_status = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if e.upstream_status is not None and 400 <= e.upstream_status < 500
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=http_status, detail=str(e))
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
        # TikTok 4xx = policy/client error → 422; TikTok 5xx or unknown → 502
        http_status = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if e.upstream_status is not None and 400 <= e.upstream_status < 500
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=http_status, detail=str(e))
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
        # TikTok 4xx = policy/client error → 422; TikTok 5xx or unknown → 502
        http_status = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if e.upstream_status is not None and 400 <= e.upstream_status < 500
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=http_status, detail=str(e))
    finally:
        await tt.close()
