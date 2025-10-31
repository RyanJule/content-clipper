from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.clip import Clip, ClipCreate, ClipUpdate
from app.services import clip_service

router = APIRouter()


@router.post("/", response_model=Clip, status_code=status.HTTP_201_CREATED)
async def create_clip(
    clip: ClipCreate, user_id: int = 1, db: Session = Depends(get_db)
):
    """Create a new clip from media"""
    try:
        return clip_service.create_clip(db, clip=clip, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[Clip])
async def list_clips(
    skip: int = 0, limit: int = 100, user_id: int = 1, db: Session = Depends(get_db)
):
    """List all clips for a user"""
    clips = clip_service.get_user_clips(db, user_id=user_id, skip=skip, limit=limit)
    return clips


@router.get("/{clip_id}", response_model=Clip)
async def get_clip(clip_id: int, db: Session = Depends(get_db)):
    """Get a specific clip"""
    clip = clip_service.get_clip(db, clip_id=clip_id)
    if clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found"
        )
    return clip


@router.put("/{clip_id}", response_model=Clip)
async def update_clip(clip_id: int, clip: ClipUpdate, db: Session = Depends(get_db)):
    """Update a clip"""
    db_clip = clip_service.update_clip(db, clip_id=clip_id, clip=clip)
    if db_clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found"
        )
    return db_clip


@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clip(clip_id: int, db: Session = Depends(get_db)):
    """Delete a clip"""
    success = clip_service.delete_clip(db, clip_id=clip_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found"
        )
    return None


@router.post("/{clip_id}/generate-content", response_model=Clip)
async def generate_clip_content(clip_id: int, db: Session = Depends(get_db)):
    """Generate AI content for a clip"""
    try:
        clip = clip_service.generate_clip_content(db, clip_id=clip_id)
        return clip
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
