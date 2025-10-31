import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.social_post import PostStatus, SocialPost
from app.schemas.social_post import SocialPostCreate, SocialPostUpdate
from app.services.clip_service import get_clip

logger = logging.getLogger(__name__)


def get_post(db: Session, post_id: int) -> Optional[SocialPost]:
    """Get post by ID"""
    return db.query(SocialPost).filter(SocialPost.id == post_id).first()


def get_user_posts(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[SocialPost]:
    """Get all posts for a user"""
    return (
        db.query(SocialPost)
        .filter(SocialPost.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_social_post(db: Session, post: SocialPostCreate, user_id: int) -> SocialPost:
    """Create a new social media post"""

    # Validate clip exists
    clip = get_clip(db, post.clip_id)
    if not clip:
        raise ValueError("Clip not found")

    # Create database record
    db_post = SocialPost(
        user_id=user_id,
        clip_id=post.clip_id,
        platform=post.platform,
        title=post.title,
        caption=post.caption,
        hashtags=json.dumps(post.hashtags) if post.hashtags else None,
        scheduled_for=post.scheduled_for,
        status=PostStatus.SCHEDULED if post.scheduled_for else PostStatus.DRAFT,
    )

    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    return db_post


def update_post(
    db: Session, post_id: int, post: SocialPostUpdate
) -> Optional[SocialPost]:
    """Update a social post"""
    db_post = get_post(db, post_id)
    if not db_post:
        return None

    update_data = post.model_dump(exclude_unset=True)

    # Handle hashtags
    if "hashtags" in update_data and update_data["hashtags"] is not None:
        update_data["hashtags"] = json.dumps(update_data["hashtags"])

    for field, value in update_data.items():
        setattr(db_post, field, value)

    db.commit()
    db.refresh(db_post)
    return db_post


def delete_post(db: Session, post_id: int) -> bool:
    """Delete a social post"""
    db_post = get_post(db, post_id)
    if not db_post:
        return False

    db.delete(db_post)
    db.commit()
    return True


def publish_post(db: Session, post_id: int) -> dict:
    """Publish a post immediately"""
    db_post = get_post(db, post_id)
    if not db_post:
        raise ValueError("Post not found")

    if db_post.status == PostStatus.PUBLISHED:
        raise ValueError("Post already published")

    # TODO: Implement actual social media API publishing
    # For now, just mark as published

    db_post.status = PostStatus.PUBLISHED
    db_post.published_at = datetime.utcnow()
    db_post.platform_post_id = f"mock_{post_id}"
    db_post.platform_url = f"https://{db_post.platform.value}.com/post/mock_{post_id}"

    db.commit()
    db.refresh(db_post)

    return {
        "success": True,
        "post_id": post_id,
        "platform_url": db_post.platform_url,
        "message": "Post published successfully",
    }
