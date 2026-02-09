from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.media import Media, MediaURLResponse, MediaUploadResponse
from app.services import media_service

router = APIRouter()


@router.post(
    "/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED
)
async def upload_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a video or audio file"""
    try:
        result = await media_service.upload_media(db, file, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


@router.get("/", response_model=List[Media])
async def list_media(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all media for current user"""
    media = media_service.get_user_media(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return media


@router.get("/{media_id}", response_model=Media)
async def get_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific media file"""
    media = media_service.get_media(db, media_id=media_id)
    if media is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )

    # Check ownership
    if media.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this media",
        )

    return media


@router.get("/{media_id}/url", response_model=MediaURLResponse)
async def get_media_url(
    media_id: int,
    expires: int = Query(default=3600, ge=60, le=86400, description="URL expiry in seconds"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a presigned URL for streaming or downloading a media file.

    The URL is temporary and expires after the specified duration (default 1 hour).
    """
    media = media_service.get_media(db, media_id=media_id)
    if media is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )

    if media.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this media",
        )

    url = media_service.get_media_url(media, expires=expires)
    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not available in storage",
        )

    return MediaURLResponse(media_id=media.id, url=url, expires_in=expires)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a media file"""
    media = media_service.get_media(db, media_id=media_id)
    if media is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )

    # Check ownership
    if media.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this media",
        )

    success = media_service.delete_media(db, media_id=media_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete media",
        )

    return None
