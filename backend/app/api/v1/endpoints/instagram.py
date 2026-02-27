"""
Instagram API Endpoints

Provides frontend-facing endpoints for Instagram Graph API features:
- Account info
- Media listing
- Comment management
- Insights/analytics
- Message management
- Direct publishing (image, carousel, video, reel)
"""

import asyncio
import io
import logging
import uuid as uuid_mod
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.core.crypto import decrypt_token
from app.core.storage import minio_client
from app.models.account import Account
from app.models.user import User
from app.services import media_service
from app.services.instagram_graph_service import (
    InstagramGraphAPI,
    InstagramGraphAPIError,
    create_instagram_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Request Schemas ====================

class CommentReplyRequest(BaseModel):
    message: str


class SendMessageRequest(BaseModel):
    recipient_id: str
    message: str


class HideCommentRequest(BaseModel):
    hide: bool = True


class PublishImageRequest(BaseModel):
    media_id: int
    caption: Optional[str] = None


class PublishCarouselRequest(BaseModel):
    media_ids: List[int]
    caption: Optional[str] = None


class PublishVideoRequest(BaseModel):
    media_id: int
    caption: Optional[str] = None


class PublishReelRequest(BaseModel):
    media_id: int
    caption: Optional[str] = None


# ==================== Helpers ====================

async def _get_instagram_service(
    current_user: User,
    db: Session,
) -> tuple:
    """Get an authenticated Instagram service and account info for the current user."""
    account = (
        db.query(Account)
        .filter(
            Account.user_id == current_user.id,
            Account.platform == "instagram",
            Account.is_active == True,
        )
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Instagram account found. Please connect your Instagram account first.",
        )

    access_token = decrypt_token(account.access_token_enc)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Instagram access token is invalid. Please reconnect your account.",
        )

    meta_info = account.meta_info or {}
    ig_account_id = meta_info.get("instagram_business_account_id")
    if not ig_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instagram Business Account ID not found. Please reconnect.",
        )

    # Use page access token if available (more permissions)
    page_token = meta_info.get("access_token")
    token = page_token if page_token else access_token

    return create_instagram_service(token), ig_account_id


# ==================== Account Info ====================

@router.get("/account")
async def get_account_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get Instagram Business Account information."""
    ig_api, ig_account_id = await _get_instagram_service(current_user, db)
    try:
        info = await ig_api.get_instagram_account_info(ig_account_id)
        return info
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


# ==================== Media ====================

@router.get("/media")
async def list_media(
    limit: int = 25,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the user's published Instagram media."""
    ig_api, ig_account_id = await _get_instagram_service(current_user, db)
    try:
        media = await ig_api.get_user_media(ig_account_id, limit=limit)
        return {"data": media}
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


@router.get("/media/{media_id}")
async def get_media_details(
    media_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get details about a specific Instagram media object."""
    ig_api, _ = await _get_instagram_service(current_user, db)
    try:
        details = await ig_api.get_media_details(media_id)
        return details
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


# ==================== Comments ====================

@router.get("/media/{media_id}/comments")
async def get_media_comments(
    media_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get comments on an Instagram media object."""
    ig_api, _ = await _get_instagram_service(current_user, db)
    try:
        comments = await ig_api.get_media_comments(media_id, limit=limit)
        return {"data": comments}
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


@router.post("/comments/{comment_id}/reply")
async def reply_to_comment(
    comment_id: str,
    request: CommentReplyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Reply to an Instagram comment."""
    ig_api, _ = await _get_instagram_service(current_user, db)
    try:
        reply_id = await ig_api.reply_to_comment(comment_id, request.message)
        return {"id": reply_id, "success": True}
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete an Instagram comment."""
    ig_api, _ = await _get_instagram_service(current_user, db)
    try:
        await ig_api.delete_comment(comment_id)
        return None
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


@router.post("/comments/{comment_id}/hide")
async def hide_comment(
    comment_id: str,
    request: HideCommentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Hide or unhide an Instagram comment."""
    ig_api, _ = await _get_instagram_service(current_user, db)
    try:
        result = await ig_api.hide_comment(comment_id, hide=request.hide)
        return {"success": result}
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


# ==================== Insights ====================

@router.get("/insights")
async def get_account_insights(
    metrics: str = "impressions,reach,profile_views",
    period: str = "day",
    since: Optional[int] = None,
    until: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get Instagram account-level insights."""
    ig_api, ig_account_id = await _get_instagram_service(current_user, db)
    try:
        metric_list = [m.strip() for m in metrics.split(",")]
        insights = await ig_api.get_account_insights(
            ig_account_id,
            metrics=metric_list,
            period=period,
            since=since,
            until=until,
        )
        return {"data": insights}
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


@router.get("/media/{media_id}/insights")
async def get_media_insights(
    media_id: str,
    metrics: str = "engagement,impressions,reach,saved",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get insights for a specific Instagram media object."""
    ig_api, _ = await _get_instagram_service(current_user, db)
    try:
        metric_list = [m.strip() for m in metrics.split(",")]
        insights = await ig_api.get_media_insights(media_id, metrics=metric_list)
        return {"data": insights}
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


# ==================== Messages ====================

@router.get("/conversations")
async def get_conversations(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get Instagram Direct message conversations."""
    ig_api, ig_account_id = await _get_instagram_service(current_user, db)
    try:
        conversations = await ig_api.get_conversations(ig_account_id, limit=limit)
        return {"data": conversations}
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get messages in an Instagram conversation."""
    ig_api, _ = await _get_instagram_service(current_user, db)
    try:
        messages = await ig_api.get_conversation_messages(conversation_id, limit=limit)
        return {"data": messages}
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


@router.post("/messages")
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Send an Instagram Direct message."""
    ig_api, ig_account_id = await _get_instagram_service(current_user, db)
    try:
        msg_id = await ig_api.send_message(
            ig_account_id, request.recipient_id, request.message
        )
        return {"id": msg_id, "success": True}
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


# ==================== Publishing Helpers ====================

_INTERNAL_HOSTNAMES = frozenset({
    "minio",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
})


def _assert_url_is_public(url: str) -> None:
    """Raise HTTP 503 if *url* resolves to an internal/Docker hostname.

    When ``MINIO_PUBLIC_URL`` is not configured the MinIO client generates
    presigned URLs with the internal Docker service name (e.g. ``minio:9000``).
    The Instagram Graph API cannot reach that host from the public internet,
    which causes the misleading error "Only photo or video can be accepted as
    media type".  Fail fast with a clear diagnostic message instead.
    """
    try:
        hostname = urlparse(url).hostname or ""
    except Exception:
        return  # unparseable — let Instagram surface the real error
    if hostname in _INTERNAL_HOSTNAMES or hostname.endswith(".local"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Media storage is not publicly accessible. "
                "Set MINIO_PUBLIC_URL to the public-facing MinIO URL "
                "(e.g. 'https://machine-systems.org/minio') so Instagram "
                "can download the media file."
            ),
        )


def _get_media_url_for_user(media_id: int, user_id: int, db: Session) -> str:
    """Retrieve a presigned URL for a media item owned by the given user.

    The URL is valid for 2 hours — sufficient for Instagram to fetch and
    process the media.

    Raises HTTPException (404/403/500) on failure.
    """
    item = media_service.get_media(db, media_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    if item.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this media",
        )
    url = media_service.get_media_url(item, expires=7200)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate a public URL for the media",
        )
    _assert_url_is_public(url)
    logger.info("Media URL for Instagram (media_id=%d): %s", media_id, url)
    return url


def _get_instagram_image_url(
    media_id: int, user_id: int, db: Session
) -> Tuple[str, Optional[str]]:
    """Return ``(presigned_url, temp_object_key)`` for an image to post to Instagram.

    Instagram's Graph API only supports JPEG images.  Any non-JPEG image
    (PNG, GIF, WebP, BMP, etc.) is converted to JPEG on the fly so that
    Instagram does not reject it with "The image format is not supported."

    If a temporary JPEG was created in MinIO, ``temp_object_key`` is set to its
    object key so the caller can delete it from MinIO after publishing.  The
    caller is responsible for always deleting the temp object in a ``finally``
    block.
    """
    item = media_service.get_media(db, media_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    if item.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this media",
        )

    mime = (item.mime_type or "").lower()
    fname = item.filename.lower()
    is_jpeg = mime == "image/jpeg" or fname.endswith(".jpg") or fname.endswith(".jpeg")

    # Convert any non-JPEG image to JPEG; Instagram only supports JPEG.
    if not is_jpeg:
        try:
            # Prefer the local copy (fast); fall back to downloading from MinIO
            # if the file has been removed from the container filesystem (e.g.
            # after a restart or when the uploads dir is not a persistent volume).
            try:
                with Image.open(item.file_path) as img:
                    rgb_img = img.convert("RGB")
                    buf = io.BytesIO()
                    rgb_img.save(buf, format="JPEG", quality=95)
                    jpeg_bytes = buf.getvalue()
            except (FileNotFoundError, OSError):
                logger.info(
                    "Local file missing for media %d — downloading from MinIO for non-JPEG→JPEG conversion",
                    media_id,
                )
                object_key = media_service._media_object_key(item.filename)
                raw = minio_client.get_object_bytes(object_key)
                if raw is None:
                    raise RuntimeError("Could not retrieve image from object storage")
                with Image.open(io.BytesIO(raw)) as img:
                    rgb_img = img.convert("RGB")
                    buf = io.BytesIO()
                    rgb_img.save(buf, format="JPEG", quality=95)
                    jpeg_bytes = buf.getvalue()

            temp_key = f"temp/instagram_{uuid_mod.uuid4()}.jpg"
            if minio_client.upload_data(jpeg_bytes, temp_key, content_type="image/jpeg"):
                url = minio_client.get_presigned_url(temp_key, expires=7200)
                if url:
                    _assert_url_is_public(url)
                    logger.info(
                        "Converted media %d (%s)→JPEG for Instagram (temp key: %s, url: %s)",
                        media_id,
                        mime or fname.rsplit(".", 1)[-1],
                        temp_key,
                        url,
                    )
                    return url, temp_key
                # Could not get a URL — clean up and fall through to original
                minio_client.delete_file(temp_key)
        except Exception as exc:
            logger.warning(
                "Non-JPEG→JPEG conversion failed for media %d: %s — falling back to original",
                media_id,
                exc,
            )

    # Original file (already JPEG, or conversion failed)
    url = media_service.get_media_url(item, expires=7200)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate a public URL for the media",
        )
    _assert_url_is_public(url)
    logger.info("Image URL for Instagram (media_id=%d): %s", media_id, url)
    return url, None


async def _wait_for_video_container(ig_api: InstagramGraphAPI, container_id: str) -> None:
    """Poll the Instagram container status until FINISHED or ERROR.

    Raises HTTPException on processing error or timeout (3 minutes).
    """
    max_attempts = 90  # 90 × 2 s = 3 minutes
    for _ in range(max_attempts):
        await asyncio.sleep(2)
        try:
            status_data = await ig_api.check_container_status(container_id)
            status_code = status_data.get("status_code", "")
            if status_code == "FINISHED":
                return
            if status_code == "ERROR":
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Instagram video processing failed: {status_data.get('status', 'unknown error')}",
                )
        except InstagramGraphAPIError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail="Timed out waiting for Instagram video processing",
    )


# ==================== Direct Publishing ====================

@router.post("/publish/image")
async def publish_image(
    request: PublishImageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Publish a single image post directly to Instagram."""
    ig_api, ig_account_id = await _get_instagram_service(current_user, db)
    temp_key: Optional[str] = None
    try:
        image_url, temp_key = _get_instagram_image_url(request.media_id, current_user.id, db)
        container_id = await ig_api.create_image_container(
            ig_account_id, image_url, caption=request.caption
        )
        media_id = await ig_api.publish_container(ig_account_id, container_id)
        return {"id": media_id, "success": True}
    except HTTPException:
        raise
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        if temp_key:
            minio_client.delete_file(temp_key)
        await ig_api.close()


@router.post("/publish/carousel")
async def publish_carousel(
    request: PublishCarouselRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Publish a carousel post (2–10 images) directly to Instagram."""
    if len(request.media_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Carousel requires at least 2 images",
        )
    if len(request.media_ids) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Carousel supports a maximum of 10 images",
        )
    ig_api, ig_account_id = await _get_instagram_service(current_user, db)
    temp_keys: List[str] = []
    try:
        # Create child containers for each image
        child_ids: List[str] = []
        for mid in request.media_ids:
            image_url, temp_key = _get_instagram_image_url(mid, current_user.id, db)
            if temp_key:
                temp_keys.append(temp_key)
            child_id = await ig_api.create_image_container(
                ig_account_id, image_url, is_carousel_item=True
            )
            child_ids.append(child_id)

        # Create the carousel container and publish
        carousel_id = await ig_api.create_carousel_container(
            ig_account_id, child_ids, caption=request.caption
        )
        media_id = await ig_api.publish_container(ig_account_id, carousel_id)
        return {"id": media_id, "success": True}
    except HTTPException:
        raise
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        for temp_key in temp_keys:
            minio_client.delete_file(temp_key)
        await ig_api.close()


@router.post("/publish/video")
async def publish_video(
    request: PublishVideoRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Publish a video post directly to Instagram."""
    ig_api, ig_account_id = await _get_instagram_service(current_user, db)
    try:
        video_url = _get_media_url_for_user(request.media_id, current_user.id, db)
        container_id = await ig_api.create_video_container(
            ig_account_id, video_url, caption=request.caption, media_type="VIDEO"
        )
        await _wait_for_video_container(ig_api, container_id)
        media_id = await ig_api.publish_container(ig_account_id, container_id)
        return {"id": media_id, "success": True}
    except HTTPException:
        raise
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()


@router.post("/publish/reel")
async def publish_reel(
    request: PublishReelRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Publish a Reel directly to Instagram."""
    ig_api, ig_account_id = await _get_instagram_service(current_user, db)
    try:
        video_url = _get_media_url_for_user(request.media_id, current_user.id, db)
        container_id = await ig_api.create_video_container(
            ig_account_id, video_url, caption=request.caption, media_type="REELS"
        )
        await _wait_for_video_container(ig_api, container_id)
        media_id = await ig_api.publish_container(ig_account_id, container_id)
        return {"id": media_id, "success": True}
    except HTTPException:
        raise
    except InstagramGraphAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await ig_api.close()
