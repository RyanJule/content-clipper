"""
LinkedIn API Endpoints

Provides endpoints for:
- Profile info
- Organization (company page) listing
- Text post publishing
- Image post publishing
- Video post publishing
- Article sharing
- Post listing and deletion
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.core.crypto import decrypt_token
from app.models.account import Account
from app.models.user import User
from app.services.linkedin_service import (
    LinkedInAPIError,
    LinkedInService,
    create_linkedin_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Request/Response Schemas ====================

class TextPostRequest(BaseModel):
    text: str
    author_urn: Optional[str] = None
    visibility: str = "PUBLIC"


class ArticlePostRequest(BaseModel):
    text: str
    article_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    author_urn: Optional[str] = None
    visibility: str = "PUBLIC"


# ==================== Helpers ====================

async def _get_linkedin_service(
    current_user: User,
    db: Session,
) -> LinkedInService:
    """Get an authenticated LinkedIn service for the current user."""
    account = (
        db.query(Account)
        .filter(
            Account.user_id == current_user.id,
            Account.platform == "linkedin",
            Account.is_active == True,
        )
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active LinkedIn account found. Please connect your LinkedIn account first.",
        )

    access_token = decrypt_token(account.access_token_enc)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="LinkedIn access token is invalid. Please reconnect your account.",
        )

    return create_linkedin_service(access_token)


def _get_default_author_urn(
    author_urn: Optional[str],
    current_user: User,
    db: Session,
) -> str:
    """Get the author URN, defaulting to the user's person URN."""
    if author_urn:
        return author_urn

    account = (
        db.query(Account)
        .filter(
            Account.user_id == current_user.id,
            Account.platform == "linkedin",
            Account.is_active == True,
        )
        .first()
    )
    if not account or not account.meta_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LinkedIn account metadata not found. Please reconnect your account.",
        )

    person_urn = account.meta_info.get("person_urn", "")
    if not person_urn:
        person_id = account.meta_info.get("id", "")
        if person_id:
            person_urn = f"urn:li:person:{person_id}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn person URN not found. Please reconnect your account.",
            )

    return person_urn


# ==================== Profile Endpoints ====================

@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated user's LinkedIn profile information."""
    li = await _get_linkedin_service(current_user, db)
    try:
        profile = await li.get_profile()
        return profile
    except LinkedInAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await li.close()


@router.get("/organizations")
async def get_organizations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get organizations (company pages) the user can post as."""
    li = await _get_linkedin_service(current_user, db)
    try:
        orgs = await li.get_organizations()
        return {"organizations": orgs}
    except LinkedInAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await li.close()


# ==================== Text Post Endpoints ====================

@router.post("/posts/text")
async def create_text_post(
    request: TextPostRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a text-only post on LinkedIn.

    Supports posting as personal profile or company page via author_urn.
    """
    li = await _get_linkedin_service(current_user, db)
    try:
        author_urn = _get_default_author_urn(request.author_urn, current_user, db)

        result = await li.create_text_post(
            author_urn=author_urn,
            text=request.text,
            visibility=request.visibility,
        )

        return {
            "success": True,
            "post_urn": result.get("post_urn", ""),
            "post_url": result.get("post_url", ""),
        }
    except LinkedInAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await li.close()


# ==================== Image Post Endpoints ====================

@router.post("/posts/image")
async def create_image_post(
    file: UploadFile = File(...),
    text: str = Form(""),
    alt_text: str = Form(""),
    author_urn: Optional[str] = Form(None),
    visibility: str = Form("PUBLIC"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a post with an image on LinkedIn.

    Accepts multipart form data with the image file and metadata.
    Supports posting as personal profile or company page via author_urn.
    """
    li = await _get_linkedin_service(current_user, db)
    try:
        resolved_author = _get_default_author_urn(author_urn, current_user, db)

        image_data = await file.read()

        # Validate image size (max 10MB for LinkedIn)
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image must be under 10MB",
            )

        content_type = file.content_type or "image/jpeg"

        result = await li.create_image_post(
            author_urn=resolved_author,
            text=text,
            image_data=image_data,
            content_type=content_type,
            alt_text=alt_text,
            visibility=visibility,
        )

        return {
            "success": True,
            "post_urn": result.get("post_urn", ""),
            "image_urn": result.get("image_urn", ""),
            "post_url": result.get("post_url", ""),
        }
    except LinkedInAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.error(f"Image post creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image post creation failed: {str(e)}",
        )
    finally:
        await li.close()


# ==================== Video Post Endpoints ====================

@router.post("/posts/video")
async def create_video_post(
    file: UploadFile = File(...),
    text: str = Form(""),
    title: str = Form(""),
    author_urn: Optional[str] = Form(None),
    visibility: str = Form("PUBLIC"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a post with a video on LinkedIn.

    Accepts multipart form data with the video file and metadata.
    Video is uploaded via LinkedIn's multipart upload protocol.
    Supports posting as personal profile or company page via author_urn.
    """
    li = await _get_linkedin_service(current_user, db)
    try:
        resolved_author = _get_default_author_urn(author_urn, current_user, db)

        video_data = await file.read()

        # Validate video size (max 200MB for LinkedIn)
        if len(video_data) > 200 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video must be under 200MB",
            )

        result = await li.create_video_post(
            author_urn=resolved_author,
            text=text,
            video_data=video_data,
            title=title,
            visibility=visibility,
        )

        return {
            "success": True,
            "post_urn": result.get("post_urn", ""),
            "video_urn": result.get("video_urn", ""),
            "post_url": result.get("post_url", ""),
        }
    except LinkedInAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.error(f"Video post creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video post creation failed: {str(e)}",
        )
    finally:
        await li.close()


# ==================== Article Post Endpoints ====================

@router.post("/posts/article")
async def create_article_post(
    request: ArticlePostRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a post sharing an article/URL on LinkedIn.

    LinkedIn will automatically fetch the article's metadata (title, description,
    thumbnail) from the URL. You can optionally override the title and description.
    """
    li = await _get_linkedin_service(current_user, db)
    try:
        author_urn = _get_default_author_urn(request.author_urn, current_user, db)

        result = await li.create_article_post(
            author_urn=author_urn,
            text=request.text,
            article_url=request.article_url,
            title=request.title or "",
            description=request.description or "",
            visibility=request.visibility,
        )

        return {
            "success": True,
            "post_urn": result.get("post_urn", ""),
            "post_url": result.get("post_url", ""),
        }
    except LinkedInAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await li.close()


# ==================== Post Management ====================

@router.get("/posts")
async def list_posts(
    author_urn: Optional[str] = None,
    count: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get recent posts for the authenticated user or a company page."""
    li = await _get_linkedin_service(current_user, db)
    try:
        resolved_author = _get_default_author_urn(author_urn, current_user, db)
        posts = await li.get_posts(author_urn=resolved_author, count=count)
        return {"posts": posts}
    except LinkedInAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await li.close()


@router.delete("/posts/{post_urn:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_urn: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a LinkedIn post by URN."""
    li = await _get_linkedin_service(current_user, db)
    try:
        await li.delete_post(post_urn)
        return None
    except LinkedInAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    finally:
        await li.close()
