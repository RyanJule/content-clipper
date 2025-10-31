import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.clip import Clip, ClipStatus
from app.schemas.clip import ClipCreate, ClipUpdate
from app.services.media_service import get_media

logger = logging.getLogger(__name__)

CLIPS_DIR = Path("/app/uploads/clips")
CLIPS_DIR.mkdir(parents=True, exist_ok=True)


def get_clip(db: Session, clip_id: int) -> Optional[Clip]:
    """Get clip by ID"""
    return db.query(Clip).filter(Clip.id == clip_id).first()


def get_user_clips(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[Clip]:
    """Get all clips for a user"""
    return (
        db.query(Clip).filter(Clip.user_id == user_id).offset(skip).limit(limit).all()
    )


def create_clip(db: Session, clip: ClipCreate, user_id: int) -> Clip:
    """Create a new clip"""

    # Validate media exists
    media = get_media(db, clip.media_id)
    if not media:
        raise ValueError("Media not found")

    # Validate timing
    if clip.end_time <= clip.start_time:
        raise ValueError("End time must be greater than start time")

    if media.duration and clip.end_time > media.duration:
        raise ValueError("End time exceeds media duration")

    # Calculate duration
    duration = clip.end_time - clip.start_time

    # Generate filename
    file_ext = os.path.splitext(media.filename)[1]
    unique_filename = f"clip_{uuid.uuid4()}{file_ext}"
    file_path = CLIPS_DIR / unique_filename

    # Create database record
    db_clip = Clip(
        user_id=user_id,
        media_id=clip.media_id,
        filename=unique_filename,
        file_path=str(file_path),
        start_time=clip.start_time,
        end_time=clip.end_time,
        duration=duration,
        title=clip.title,
        description=clip.description,
        tags=json.dumps(clip.tags) if clip.tags else None,
        hashtags=json.dumps(clip.hashtags) if clip.hashtags else None,
        status=ClipStatus.PENDING,
        is_auto_generated=False,
    )

    db.add(db_clip)
    db.commit()
    db.refresh(db_clip)

    # TODO: Trigger background task to actually create the clip file using FFmpeg

    return db_clip


def update_clip(db: Session, clip_id: int, clip: ClipUpdate) -> Optional[Clip]:
    """Update a clip"""
    db_clip = get_clip(db, clip_id)
    if not db_clip:
        return None

    update_data = clip.model_dump(exclude_unset=True)

    # Handle tags and hashtags
    if "tags" in update_data and update_data["tags"] is not None:
        update_data["tags"] = json.dumps(update_data["tags"])

    if "hashtags" in update_data and update_data["hashtags"] is not None:
        update_data["hashtags"] = json.dumps(update_data["hashtags"])

    for field, value in update_data.items():
        setattr(db_clip, field, value)

    db.commit()
    db.refresh(db_clip)
    return db_clip


def delete_clip(db: Session, clip_id: int) -> bool:
    """Delete a clip"""
    db_clip = get_clip(db, clip_id)
    if not db_clip:
        return False

    # Delete physical file
    try:
        if os.path.exists(db_clip.file_path):
            os.remove(db_clip.file_path)
    except Exception as e:
        logger.error(f"Error deleting clip file: {e}")

    # Delete from database
    db.delete(db_clip)
    db.commit()
    return True


def generate_clip_content(db: Session, clip_id: int) -> Clip:
    """Generate AI content for a clip"""
    db_clip = get_clip(db, clip_id)
    if not db_clip:
        raise ValueError("Clip not found")

    # TODO: Implement actual AI generation using OpenAI
    # For now, use placeholder content

    db_clip.title = f"Auto-generated clip {clip_id}"
    db_clip.description = "This is an auto-generated description for the clip."
    db_clip.tags = json.dumps(["auto", "generated", "content"])
    db_clip.hashtags = json.dumps(["#auto", "#generated", "#clip"])

    db.commit()
    db.refresh(db_clip)
    return db_clip
