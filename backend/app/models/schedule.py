from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ContentSchedule(Base):
    __tablename__ = "content_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_id = Column(
        Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )

    # Schedule metadata
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    # Schedule type: 'custom', 'suggested', 'optimal'
    schedule_type = Column(String(50), default="custom")

    # Days of week (JSON array): [1,2,3,4,5] for Mon-Fri
    days_of_week = Column(JSON, nullable=False)

    # Times of day (JSON array): ["09:00", "13:00", "18:00"]
    posting_times = Column(JSON, nullable=False)

    # Timezone
    timezone = Column(String(50), default="UTC")

    # Performance metrics
    engagement_score = Column(Integer, nullable=True)  # 0-100
    growth_rate = Column(Integer, nullable=True)  # percentage

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="schedules")
    account = relationship("Account", back_populates="schedules")
    scheduled_posts = relationship(
        "ScheduledPost", back_populates="schedule", cascade="all, delete-orphan"
    )


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    schedule_id = Column(
        Integer, ForeignKey("content_schedules.id", ondelete="CASCADE"), nullable=False
    )
    clip_id = Column(
        Integer, ForeignKey("clips.id", ondelete="SET NULL"), nullable=True
    )

    # Scheduled info
    scheduled_for = Column(DateTime, nullable=False, index=True)
    posted_at = Column(DateTime, nullable=True)

    # Content
    caption = Column(String(2000), nullable=True)
    hashtags = Column(JSON, nullable=True)  # Array of hashtags

    # Status: 'pending', 'content_ready', 'scheduled', 'posted', 'failed'
    status = Column(String(50), default="pending")

    # Platform-specific data
    platform_post_id = Column(String(255), nullable=True)
    platform_url = Column(String(500), nullable=True)
    error_message = Column(String(1000), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    schedule = relationship("ContentSchedule", back_populates="scheduled_posts")
    clip = relationship("Clip")
