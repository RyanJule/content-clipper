"""
YouTube API Endpoints

Provides endpoints for:
- Channel info
- Video listing and details
- Video upload (resumable)
- Shorts upload
- Community posts
- Thumbnail upload
- Video comments
- Video categories
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
from app.services.youtube_service import (
    YouTubeAPIError,
    YouTubeService,
    create_youtube_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Request/Response Schemas ====================

class VideoUploadRequest(BaseModel):
    title: str
    description: str = ""
    tags: Optional[List[str]] = None
    category_id: str = "22"
    privacy_status: str = "private"
    is_short: bool = False
    scheduled_start_time: Optional[str] = None
    notify_subscribers: bool = True


class VideoUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category_id: Optional[str] = None
    privacy_status: Optional[str] = None


class CommunityPostRequest(BaseModel):
    text: str


class CommentRequest(BaseModel):
    text: str


# ==================== Helpers ====================

async def _get_youtube_service(
    current_user: User,
    db: Session,
) -> YouTubeService:
    """Get an authenticated YouTube service for the current user."""
    account = (
        db.query(Account)
        .filter(
            Account.user_id == current_user.id,
            Account.platform == "youtube",
            Account.is_active == True,
        )
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active YouTube account found. Please connect your YouTube account first.",
        )

    # Refresh the token if it is expired or about to expire
    if account.token_expires_at:
        now = datetime.utcnow()
        buffer = timedelta(minutes=5)
        if now + buffer >= account.token_expires_at:
            logger.info(
                f"YouTube token expiring soon for account {account.id}, refreshing..."
            )
            try:
                account = await refresh_account_token(db, account)
            except Exception as e:
                logger.error(f"Failed to refresh YouTube token: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="YouTube access token has expired and could not be refreshed. Please reconnect your account.",
                )

    access_token = decrypt_token(account.access_token_enc)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="YouTube access token is invalid. Please reconnect your account.",
        )

    return create_youtube_service(access_token)


# ==================== Channel Endpoints ====================

@router.get("/channel")
async def get_channel_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated user's YouTube channel information."""
    yt = await _get_youtube_service(current_user, db)
    try:
        channel = await yt.get_channel_info()
        return channel
    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()


@router.get("/videos")
async def list_videos(
    max_results: int = 25,
    page_token: Optional[str] = None,
    order: str = "date",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List videos from the user's YouTube channel."""
    yt = await _get_youtube_service(current_user, db)
    try:
        videos = await yt.get_channel_videos(
            max_results=max_results,
            page_token=page_token,
            order=order,
        )
        return videos
    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()


@router.get("/videos/{video_id}")
async def get_video(
    video_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get details for a specific YouTube video."""
    yt = await _get_youtube_service(current_user, db)
    try:
        video = await yt.get_video_details(video_id)
        return video
    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()


# ==================== Video Upload Endpoints ====================

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    category_id: str = Form("22"),
    privacy_status: str = Form("private"),
    is_short: bool = Form(False),
    notify_subscribers: bool = Form(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload a video to YouTube using resumable upload.

    Accepts multipart form data with the video file and metadata.
    For Shorts, set is_short=true (video must be vertical and < 60s).
    """
    yt = await _get_youtube_service(current_user, db)
    try:
        # Parse tags from comma-separated string
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

        # Read the file content
        video_data = await file.read()

        if is_short:
            result = await yt.upload_short_bytes(
                video_data=video_data,
                title=title,
                description=description,
                tags=tag_list,
                privacy_status=privacy_status,
                notify_subscribers=notify_subscribers,
            )
        else:
            result = await yt.upload_video_bytes(
                video_data=video_data,
                title=title,
                description=description,
                tags=tag_list,
                category_id=category_id,
                privacy_status=privacy_status,
                is_short=False,
                notify_subscribers=notify_subscribers,
            )

        video_id = result.get("id")
        platform_url = f"https://www.youtube.com/watch?v={video_id}"
        if is_short:
            platform_url = f"https://www.youtube.com/shorts/{video_id}"

        return {
            "success": True,
            "video_id": video_id,
            "url": platform_url,
            "video": result,
        }

    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.error(f"Video upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )
    finally:
        await yt.close()


@router.post("/upload/short")
async def upload_short(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    privacy_status: str = Form("public"),
    notify_subscribers: bool = Form(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload a YouTube Short.

    Requirements:
    - Vertical video (9:16 aspect ratio)
    - Max 60 seconds duration
    - #Shorts tag is added automatically
    """
    yt = await _get_youtube_service(current_user, db)
    try:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

        video_data = await file.read()

        result = await yt.upload_short_bytes(
            video_data=video_data,
            title=title,
            description=description,
            tags=tag_list,
            privacy_status=privacy_status,
            notify_subscribers=notify_subscribers,
        )

        video_id = result.get("id")

        return {
            "success": True,
            "video_id": video_id,
            "url": f"https://www.youtube.com/shorts/{video_id}",
            "video": result,
        }

    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.error(f"Short upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )
    finally:
        await yt.close()


# ==================== Video Management ====================

@router.put("/videos/{video_id}")
async def update_video(
    video_id: str,
    request: VideoUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update video metadata (title, description, tags, privacy)."""
    yt = await _get_youtube_service(current_user, db)
    try:
        result = await yt.update_video(
            video_id=video_id,
            title=request.title,
            description=request.description,
            tags=request.tags,
            category_id=request.category_id,
            privacy_status=request.privacy_status,
        )
        return result
    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()


@router.delete("/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a YouTube video."""
    yt = await _get_youtube_service(current_user, db)
    try:
        await yt.delete_video(video_id)
        return None
    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()


# ==================== Thumbnail Endpoints ====================

@router.post("/videos/{video_id}/thumbnail")
async def set_thumbnail(
    video_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload a custom thumbnail for a video.

    Requirements:
    - Image: 1280x720 (16:9 aspect ratio)
    - Max file size: 2MB
    - Formats: JPG, PNG, GIF
    - Account must be verified for custom thumbnails
    """
    yt = await _get_youtube_service(current_user, db)
    try:
        image_data = await file.read()

        # Validate file size (2MB max)
        if len(image_data) > 2 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thumbnail must be under 2MB",
            )

        content_type = file.content_type or "image/png"

        result = await yt.set_thumbnail(
            video_id=video_id,
            image_data=image_data,
            content_type=content_type,
        )

        return {
            "success": True,
            "video_id": video_id,
            "thumbnail": result,
        }

    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()


# ==================== Community Posts ====================

@router.post("/community")
async def create_community_post(
    request: CommunityPostRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a YouTube community post.

    Requires channel to have 500+ subscribers with Community tab enabled.
    """
    yt = await _get_youtube_service(current_user, db)
    try:
        result = await yt.create_community_post(text=request.text)
        return {
            "success": True,
            "post": result,
        }
    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()


# ==================== Comments ====================

@router.get("/videos/{video_id}/comments")
async def get_video_comments(
    video_id: str,
    max_results: int = 20,
    order: str = "relevance",
    page_token: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get comment threads for a video."""
    yt = await _get_youtube_service(current_user, db)
    try:
        comments = await yt.get_video_comments(
            video_id=video_id,
            max_results=max_results,
            order=order,
            page_token=page_token,
        )
        return comments
    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()


@router.post("/videos/{video_id}/comments")
async def post_comment(
    video_id: str,
    request: CommentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Post a top-level comment on a video."""
    yt = await _get_youtube_service(current_user, db)
    try:
        result = await yt.post_comment(video_id=video_id, text=request.text)
        return result
    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()


@router.post("/comments/{comment_id}/reply")
async def reply_to_comment(
    comment_id: str,
    request: CommentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Reply to a comment."""
    yt = await _get_youtube_service(current_user, db)
    try:
        result = await yt.reply_to_comment(parent_id=comment_id, text=request.text)
        return result
    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()


# ==================== Analytics ====================

@router.get("/videos/{video_id}/stats")
async def get_video_stats(
    video_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get statistics for a specific video."""
    yt = await _get_youtube_service(current_user, db)
    try:
        stats = await yt.get_video_stats(video_id)
        return stats
    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()


# ==================== Categories ====================

@router.get("/categories")
async def get_video_categories(
    region_code: str = "US",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get available video categories for a region."""
    yt = await _get_youtube_service(current_user, db)
    try:
        categories = await yt.get_video_categories(region_code=region_code)
        return {"categories": categories}
    except YouTubeAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await yt.close()
