from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.media import MediaStatus, MediaType


class MediaBase(BaseModel):
    filename: str
    original_filename: str


class MediaCreate(MediaBase):
    media_type: MediaType


class MediaUpdate(BaseModel):
    status: Optional[MediaStatus] = None
    transcription: Optional[str] = None


class Media(MediaBase):
    id: int
    user_id: int
    file_path: str
    file_size: int
    mime_type: str
    media_type: MediaType
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    status: MediaStatus
    transcription: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MediaUploadResponse(BaseModel):
    media_id: int
    filename: str
    status: str
    message: str
