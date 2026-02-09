from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.clip import ClipStatus


class ClipBase(BaseModel):
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., ge=0)


class ClipCreate(ClipBase):
    media_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None


class ClipUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    status: Optional[ClipStatus] = None


class Clip(ClipBase):
    id: int
    user_id: int
    media_id: int
    filename: str
    file_path: str
    file_size: Optional[int] = None
    duration: float
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    hashtags: Optional[str] = None
    status: ClipStatus
    is_auto_generated: bool
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClipURLResponse(BaseModel):
    clip_id: int
    url: str
    expires_in: int  # seconds until URL expires
