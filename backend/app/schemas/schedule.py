from datetime import datetime, time
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ContentScheduleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    schedule_type: str = "custom"  # custom, suggested, optimal
    days_of_week: List[int] = Field(..., description="Days of week: 0=Monday, 6=Sunday")
    posting_times: List[str] = Field(..., description="Times in HH:MM format")
    timezone: str = "UTC"


class ContentScheduleCreate(ContentScheduleBase):
    account_id: int


class ContentScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    days_of_week: Optional[List[int]] = None
    posting_times: Optional[List[str]] = None
    timezone: Optional[str] = None


class ContentSchedule(ContentScheduleBase):
    id: int
    user_id: int
    account_id: int
    engagement_score: Optional[int] = None
    growth_rate: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduledPostBase(BaseModel):
    scheduled_for: datetime
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None


class ScheduledPostCreate(ScheduledPostBase):
    schedule_id: int
    clip_id: Optional[int] = None


class ScheduledPostUpdate(BaseModel):
    scheduled_for: Optional[datetime] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    status: Optional[str] = None
    clip_id: Optional[int] = None


class ScheduledPost(ScheduledPostBase):
    id: int
    user_id: int
    schedule_id: int
    clip_id: Optional[int] = None
    posted_at: Optional[datetime] = None
    status: str
    platform_post_id: Optional[str] = None
    platform_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CalendarDay(BaseModel):
    date: str  # YYYY-MM-DD
    posts_needed: int
    posts_ready: int
    posts_scheduled: int
    posts: List[ScheduledPost]


class ScheduleSuggestion(BaseModel):
    name: str
    description: str
    days_of_week: List[int]
    posting_times: List[str]
    estimated_engagement: int
    estimated_growth: int
    reasoning: str
