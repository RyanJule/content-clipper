from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.social_post import PostStatus, SocialPlatform


class SocialPostBase(BaseModel):
    platform: SocialPlatform
    title: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None


class SocialPostCreate(SocialPostBase):
    clip_id: int
    scheduled_for: Optional[datetime] = None


class SocialPostUpdate(BaseModel):
    title: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    scheduled_for: Optional[datetime] = None
    status: Optional[PostStatus] = None


class SocialPost(SocialPostBase):
    id: int
    user_id: int
    clip_id: int
    scheduled_for: Optional[datetime] = None
    published_at: Optional[datetime] = None
    status: PostStatus
    platform_post_id: Optional[str] = None
    platform_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
