import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClipStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Clip(Base):
    __tablename__ = "clips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)

    # Clip information
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)

    # Clip timing
    start_time = Column(Float, nullable=False)  # in seconds
    end_time = Column(Float, nullable=False)  # in seconds
    duration = Column(Float, nullable=False)  # in seconds

    # AI-generated content
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array
    hashtags = Column(Text, nullable=True)  # JSON array

    # Processing
    status = Column(Enum(ClipStatus), default=ClipStatus.PENDING)
    is_auto_generated = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="clips")
    source_media = relationship("Media", back_populates="clips")
    social_posts = relationship(
        "SocialPost", back_populates="clip", cascade="all, delete-orphan"
    )
