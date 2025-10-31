from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.media import Media, MediaUploadResponse
from app.services import media_service

router = APIRouter()


@router.post(
    "/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED
)
async def upload_media(
    file: UploadFile = File(...),
    user_id: int = 1,  # TODO: Get from auth token
    db: Session = Depends(get_db),
):
    """Upload a video or audio file"""
    try:
        result = await media_service.upload_media(db, file, user_id)
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
    user_id: int = 1,  # TODO: Get from auth token
    db: Session = Depends(get_db),
):
    """List all media for a user"""
    media = media_service.get_user_media(db, user_id=user_id, skip=skip, limit=limit)
    return media


@router.get("/{media_id}", response_model=Media)
async def get_media(media_id: int, db: Session = Depends(get_db)):
    """Get a specific media file"""
    media = media_service.get_media(db, media_id=media_id)
    if media is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )
    return media


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(media_id: int, db: Session = Depends(get_db)):
    """Delete a media file"""
    success = media_service.delete_media(db, media_id=media_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )
    return None
