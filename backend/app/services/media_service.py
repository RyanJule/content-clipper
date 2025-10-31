import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.storage import minio_client
from app.models.media import Media, MediaStatus, MediaType
from app.schemas.media import MediaUploadResponse

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_media(db: Session, media_id: int) -> Optional[Media]:
    """Get media by ID"""
    return db.query(Media).filter(Media.id == media_id).first()


def get_user_media(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[Media]:
    """Get all media for a user"""
    return (
        db.query(Media).filter(Media.user_id == user_id).offset(skip).limit(limit).all()
    )


async def upload_media(
    db: Session, file: UploadFile, user_id: int
) -> MediaUploadResponse:
    """Upload and process media file"""

    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext in settings.ALLOWED_VIDEO_FORMATS:
        media_type = MediaType.VIDEO
    elif file_ext in settings.ALLOWED_AUDIO_FORMATS:
        media_type = MediaType.AUDIO
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file locally
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        file_size = len(contents)

        # Validate file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            os.remove(file_path)
            raise ValueError(
                f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes"
            )

    except Exception as e:
        logger.error(f"Error saving file: {e}")
        if file_path.exists():
            os.remove(file_path)
        raise

    # Create database record
    db_media = Media(
        user_id=user_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        media_type=media_type,
        status=MediaStatus.PROCESSING,
    )

    db.add(db_media)
    db.commit()
    db.refresh(db_media)

    # TODO: Trigger background task for processing (transcription, metadata extraction)
    # For now, just mark as ready
    db_media.status = MediaStatus.READY
    db_media.processed_at = datetime.utcnow()
    db.commit()

    return MediaUploadResponse(
        media_id=db_media.id,
        filename=unique_filename,
        status="success",
        message="Media uploaded successfully",
    )


def delete_media(db: Session, media_id: int) -> bool:
    """Delete a media file"""
    db_media = get_media(db, media_id)
    if not db_media:
        return False

    # Delete physical file
    try:
        if os.path.exists(db_media.file_path):
            os.remove(db_media.file_path)
    except Exception as e:
        logger.error(f"Error deleting file: {e}")

    # Delete from database
    db.delete(db_media)
    db.commit()
    return True
