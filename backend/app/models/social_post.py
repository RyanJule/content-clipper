import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class SocialPlatform(str, enum.Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class SocialPost(Base):
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    clip_id = Column(Integer, ForeignKey("clips.id"), nullable=False)

    # Platform information
    platform = Column(Enum(SocialPlatform), nullable=False)

    # Post content
    title = Column(String, nullable=True)
    caption = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)  # JSON array

    # Scheduling
    scheduled_for = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)

    # Status
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT)
    platform_post_id = Column(String, nullable=True)  # ID from social platform
    platform_url = Column(String, nullable=True)  # URL to post on platform
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="social_posts")
    clip = relationship("Clip", back_populates="social_posts")
