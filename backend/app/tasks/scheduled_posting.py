"""
Celery task to publish scheduled posts at their scheduled_for time.

Runs every minute via Celery Beat. Picks up ScheduledPosts with
status='scheduled' whose scheduled_for time has passed, and publishes
them via the appropriate platform API.
"""

import logging
from datetime import datetime

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.schedule import ContentSchedule, ScheduledPost

logger = logging.getLogger(__name__)


def _get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


@shared_task(name="app.tasks.scheduled_posting.publish_scheduled_posts")
def publish_scheduled_posts():
    """
    Publish all ScheduledPosts whose scheduled_for time has arrived.

    Called every minute by Celery Beat. Updates post status to 'posted'
    or 'failed' after attempting publication.
    """
    db = _get_db()
    now = datetime.utcnow()

    try:
        due_posts = (
            db.query(ScheduledPost)
            .filter(
                ScheduledPost.status == "scheduled",
                ScheduledPost.scheduled_for <= now,
            )
            .all()
        )

        if not due_posts:
            return {"published": 0, "failed": 0}

        published = 0
        failed = 0

        for post in due_posts:
            try:
                _publish_post(db, post)
                post.status = "posted"
                post.posted_at = datetime.utcnow()
                published += 1
                logger.info("Published scheduled post %d", post.id)
            except Exception as exc:
                post.status = "failed"
                post.error_message = str(exc)[:1000]
                failed += 1
                logger.error("Failed to publish scheduled post %d: %s", post.id, exc)

        db.commit()
        return {"published": published, "failed": failed}

    finally:
        db.close()


def _publish_post(db: Session, post: ScheduledPost) -> None:
    """
    Dispatch to the correct platform publisher based on the schedule's account.
    Raises an exception on failure so the caller can mark the post as failed.
    """
    schedule: ContentSchedule = (
        db.query(ContentSchedule).filter(ContentSchedule.id == post.schedule_id).first()
    )
    if not schedule:
        raise ValueError(f"ContentSchedule {post.schedule_id} not found")

    account = schedule.account
    if not account:
        raise ValueError(f"Account for schedule {schedule.id} not found")

    platform = account.platform.lower() if account.platform else ""

    if platform == "instagram":
        _publish_instagram(db, post, account)
    elif platform == "youtube":
        _publish_youtube(db, post, account)
    elif platform == "tiktok":
        _publish_tiktok(db, post, account)
    else:
        raise ValueError(f"Unsupported platform for scheduled posting: {platform}")


def _publish_instagram(db: Session, post: ScheduledPost, account) -> None:
    """Publish a scheduled post to Instagram."""
    from app.core.crypto import decrypt_token
    from app.services.instagram_service import InstagramService

    access_token = decrypt_token(account.access_token)
    ig_user_id = account.platform_account_id

    service = InstagramService(access_token=access_token, ig_user_id=ig_user_id)

    clip = post.clip
    if clip:
        # Post the clip's media
        media_url = clip.file_path
        caption = post.caption or ""
        if post.hashtags:
            caption = f"{caption} {' '.join(post.hashtags)}".strip()
        service.publish_image_from_url(media_url, caption)
    else:
        raise ValueError(f"No clip assigned to scheduled post {post.id}")


def _publish_youtube(db: Session, post: ScheduledPost, account) -> None:
    """Publish a scheduled post to YouTube."""
    # YouTube scheduled uploads are typically handled at upload time via the API
    # (set publishAt in snippet). This is a placeholder for future implementation.
    raise NotImplementedError("YouTube scheduled posting not yet implemented")


def _publish_tiktok(db: Session, post: ScheduledPost, account) -> None:
    """Publish a scheduled post to TikTok."""
    # TikTok scheduled posting is a placeholder for future implementation.
    raise NotImplementedError("TikTok scheduled posting not yet implemented")
