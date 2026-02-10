"""
Instagram API Endpoints

Provides frontend-facing endpoints for Instagram Graph API features:
- Account info
- Media listing
- Comment management
- Insights/analytics
- Message management
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.core.crypto import decrypt_token
from app.models.account import Account
from app.models.user import User
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
