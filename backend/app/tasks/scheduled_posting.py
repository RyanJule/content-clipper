"""
Celery task to publish scheduled posts.

Runs every minute via Celery Beat. Picks up any ScheduledPost with
status='scheduled' whose scheduled_for <= now and publishes it via the
appropriate platform API, then marks it as 'posted' or 'failed'.
"""

import logging
from datetime import datetime

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_token
from app.core.database import SessionLocal
from app.models.account import Account
from app.models.clip import Clip
from app.models.schedule import ContentSchedule, ScheduledPost

logger = logging.getLogger(__name__)


def _get_account_token(db: Session, schedule: ContentSchedule) -> str | None:
    account: Account | None = db.query(Account).filter(Account.id == schedule.account_id).first()
    if not account or not account.access_token:
        return None
    try:
        return decrypt_token(account.access_token)
    except Exception:
        return None


def _publish_instagram(post: ScheduledPost, schedule: ContentSchedule, db: Session) -> str:
    """Publish a ScheduledPost to Instagram and return the platform post id."""
    from app.services.instagram_graph_service import InstagramGraphAPI

    account: Account = db.query(Account).filter(Account.id == schedule.account_id).first()
    if not account:
        raise ValueError("Account not found")

    token = decrypt_token(account.access_token)
    ig_user_id = account.account_id  # stored Instagram user id

    clip: Clip | None = db.query(Clip).filter(Clip.id == post.clip_id).first() if post.clip_id else None
    media_url = clip.output_url if clip else None
    if not media_url:
        raise ValueError("No media URL available for this post")

    api = InstagramGraphAPI(access_token=token, instagram_user_id=ig_user_id)

    import asyncio

    caption = post.caption or ""
    if post.hashtags:
        caption = caption + "\n" + " ".join(f"#{h}" for h in post.hashtags)

    async def _publish():
        if media_url.lower().endswith((".mp4", ".mov")):
            result = await api.publish_video(media_url=media_url, caption=caption)
        else:
            result = await api.publish_photo(image_url=media_url, caption=caption)
        return result

    result = asyncio.run(_publish())
    return result.get("id", "unknown")


def _publish_youtube(post: ScheduledPost, schedule: ContentSchedule, db: Session) -> str:
    """Publish a ScheduledPost to YouTube and return the video id."""
    from app.services.youtube_service import create_youtube_service

    account: Account = db.query(Account).filter(Account.id == schedule.account_id).first()
    if not account:
        raise ValueError("Account not found")

    clip: Clip | None = db.query(Clip).filter(Clip.id == post.clip_id).first() if post.clip_id else None
    if not clip or not clip.output_url:
        raise ValueError("No media URL available for this post")

    token = decrypt_token(account.access_token)
    yt_service = create_youtube_service(access_token=token, refresh_token=decrypt_token(account.refresh_token) if account.refresh_token else None)

    caption = post.caption or ""
    result = yt_service.upload_video_from_url(
        video_url=clip.output_url,
        title=caption[:100] or "Scheduled Post",
        description=caption,
        privacy_status="public",
    )
    return result.get("video_id", "unknown")


def _publish_tiktok(post: ScheduledPost, schedule: ContentSchedule, db: Session) -> str:
    """Publish a ScheduledPost to TikTok and return the publish id."""
    from app.services.tiktok_service import create_tiktok_service

    account: Account = db.query(Account).filter(Account.id == schedule.account_id).first()
    if not account:
        raise ValueError("Account not found")

    clip: Clip | None = db.query(Clip).filter(Clip.id == post.clip_id).first() if post.clip_id else None
    if not clip or not clip.output_url:
        raise ValueError("No media URL available for this post")

    token = decrypt_token(account.access_token)
    tt_service = create_tiktok_service(access_token=token)

    caption = post.caption or ""
    result = tt_service.publish_video_from_url(
        video_url=clip.output_url,
        title=caption[:150] or "Scheduled Post",
        privacy_level="PUBLIC_TO_EVERYONE",
    )
    return result.get("publish_id", "unknown")


PLATFORM_PUBLISHERS = {
    "instagram": _publish_instagram,
    "youtube": _publish_youtube,
    "tiktok": _publish_tiktok,
}


@shared_task(name="app.tasks.scheduled_posting.publish_due_posts")
def publish_due_posts():
    """Publish all ScheduledPosts that are due (status=scheduled, scheduled_for <= now)."""
    db: Session = SessionLocal()
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
            schedule: ContentSchedule | None = (
                db.query(ContentSchedule).filter(ContentSchedule.id == post.schedule_id).first()
            )
            if not schedule:
                post.status = "failed"
                post.error_message = "Schedule not found"
                db.commit()
                failed += 1
                continue

            account: Account | None = (
                db.query(Account).filter(Account.id == schedule.account_id).first()
            )
            if not account:
                post.status = "failed"
                post.error_message = "Account not found"
                db.commit()
                failed += 1
                continue

            platform = account.platform.lower() if account.platform else ""
            publisher = PLATFORM_PUBLISHERS.get(platform)

            if not publisher:
                post.status = "failed"
                post.error_message = f"No publisher for platform: {platform}"
                db.commit()
                failed += 1
                continue

            try:
                platform_post_id = publisher(post, schedule, db)
                post.status = "posted"
                post.posted_at = datetime.utcnow()
                post.platform_post_id = platform_post_id
                post.error_message = None
                db.commit()
                published += 1
                logger.info("Published scheduled post %d to %s (id=%s)", post.id, platform, platform_post_id)
            except Exception as exc:
                post.status = "failed"
                post.error_message = str(exc)[:900]
                db.commit()
                failed += 1
                logger.exception("Failed to publish scheduled post %d: %s", post.id, exc)

        return {"published": published, "failed": failed}

    finally:
        db.close()
