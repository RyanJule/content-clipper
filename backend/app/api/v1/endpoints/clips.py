from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.clip import Clip, ClipCreate, ClipURLResponse, ClipUpdate
from app.services import clip_service

router = APIRouter()


@router.post("/", response_model=Clip, status_code=status.HTTP_201_CREATED)
async def create_clip(
    clip: ClipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new clip from media"""
    try:
        return clip_service.create_clip(db, clip=clip, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[Clip])
async def list_clips(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all clips for current user"""
    clips = clip_service.get_user_clips(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return clips


@router.get("/{clip_id}", response_model=Clip)
async def get_clip(
    clip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific clip"""
    clip = clip_service.get_clip(db, clip_id=clip_id)
    if clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found"
        )

    # Check ownership
    if clip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this clip",
        )

    return clip


@router.get("/{clip_id}/url", response_model=ClipURLResponse)
async def get_clip_url(
    clip_id: int,
    expires: int = Query(default=3600, ge=60, le=86400, description="URL expiry in seconds"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a presigned URL for streaming or downloading a clip file.

    The URL is temporary and expires after the specified duration (default 1 hour).
    """
    clip = clip_service.get_clip(db, clip_id=clip_id)
    if clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found"
        )

    if clip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this clip",
        )

    url = clip_service.get_clip_url(clip, expires=expires)
    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip file not available in storage",
        )

    return ClipURLResponse(clip_id=clip.id, url=url, expires_in=expires)


@router.put("/{clip_id}", response_model=Clip)
async def update_clip(
    clip_id: int,
    clip: ClipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a clip"""
    db_clip = clip_service.get_clip(db, clip_id=clip_id)
    if db_clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found"
        )

    # Check ownership
    if db_clip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this clip",
        )

    db_clip = clip_service.update_clip(db, clip_id=clip_id, clip=clip)
    return db_clip


@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clip(
    clip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a clip"""
    clip = clip_service.get_clip(db, clip_id=clip_id)
    if clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found"
        )

    # Check ownership
    if clip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this clip",
        )

    success = clip_service.delete_clip(db, clip_id=clip_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete clip",
        )

    return None


@router.post("/{clip_id}/generate-content", response_model=Clip)
async def generate_clip_content(
    clip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate AI content for a clip"""
    clip = clip_service.get_clip(db, clip_id=clip_id)
    if clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found"
        )

    # Check ownership
    if clip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this clip",
        )

    try:
        clip = clip_service.generate_clip_content(db, clip_id=clip_id)
        return clip
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
