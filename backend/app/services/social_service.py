import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.social_post import PostStatus, SocialPost, SocialPlatform
from app.models.account import Account
from app.schemas.social_post import SocialPostCreate, SocialPostUpdate
from app.services.clip_service import get_clip
from app.services.instagram_graph_service import (
    InstagramGraphAPI,
    InstagramGraphAPIError
)
from app.services.youtube_service import (
    YouTubeService,
    YouTubeAPIError,
    create_youtube_service,
)
from app.services.tiktok_service import (
    TikTokService,
    TikTokAPIError,
    create_tiktok_service,
)
from app.core.crypto import decrypt_token

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


async def publish_post(db: Session, post_id: int) -> dict:
    """Publish a post immediately"""
    db_post = get_post(db, post_id)
    if not db_post:
        raise ValueError("Post not found")

    if db_post.status == PostStatus.PUBLISHED:
        raise ValueError("Post already published")

    # Get the clip to access media
    clip = get_clip(db, db_post.clip_id)
    if not clip:
        raise ValueError("Clip not found")

    # Get the user's connected account for this platform
    account = (
        db.query(Account)
        .filter(
            Account.user_id == db_post.user_id,
            Account.platform == db_post.platform.value,
            Account.is_active == True
        )
        .first()
    )

    if not account:
        raise ValueError(f"No active {db_post.platform.value} account found")

    try:
        # Mark as publishing
        db_post.status = PostStatus.PUBLISHING
        db.commit()

        # Publish based on platform
        if db_post.platform == SocialPlatform.INSTAGRAM:
            result = await _publish_to_instagram(db_post, clip, account)
        elif db_post.platform == SocialPlatform.YOUTUBE:
            result = await _publish_to_youtube(db_post, clip, account)
        elif db_post.platform == SocialPlatform.TIKTOK:
            result = await _publish_to_tiktok(db_post, clip, account)
        else:
            # For other platforms, use mock implementation for now
            result = {
                "platform_post_id": f"mock_{post_id}",
                "platform_url": f"https://{db_post.platform.value}.com/post/mock_{post_id}"
            }

        # Update post with success
        db_post.status = PostStatus.PUBLISHED
        db_post.published_at = datetime.utcnow()
        db_post.platform_post_id = result["platform_post_id"]
        db_post.platform_url = result.get("platform_url", "")
        db_post.error_message = None

        db.commit()
        db.refresh(db_post)

        return {
            "success": True,
            "post_id": post_id,
            "platform_url": db_post.platform_url,
            "message": "Post published successfully",
        }

    except Exception as e:
        logger.error(f"Failed to publish post {post_id}: {str(e)}")

        # Mark as failed
        db_post.status = PostStatus.FAILED
        db_post.error_message = str(e)
        db.commit()

        return {
            "success": False,
            "post_id": post_id,
            "error": str(e),
            "message": "Failed to publish post",
        }


async def _publish_to_instagram(
    post: SocialPost,
    clip,
    account: Account
) -> dict:
    """
    Publish a post to Instagram using Graph API.

    Uses permission: instagram_business_content_publish

    Args:
        post: Social post object
        clip: Clip object containing media
        account: Connected Instagram account

    Returns:
        Dictionary with platform_post_id and platform_url
    """
    # Decrypt access token
    access_token = decrypt_token(account.access_token_enc)
    if not access_token:
        raise ValueError("Invalid access token")

    # Get Instagram Business Account ID from meta_info
    meta_info = account.meta_info or {}
    ig_account_id = meta_info.get("instagram_business_account_id")

    if not ig_account_id:
        raise ValueError("Instagram Business Account ID not found. Please reconnect your account.")

    # Create Instagram API client
    ig_api = InstagramGraphAPI(access_token)

    try:
        # Prepare caption with hashtags
        caption = post.caption or ""
        if post.hashtags:
            hashtags_list = json.loads(post.hashtags) if isinstance(post.hashtags, str) else post.hashtags
            caption = f"{caption}\n\n{' '.join(hashtags_list)}"

        # Get media URL from clip
        # Assuming clip has a media_url or we need to construct it
        media_url = getattr(clip, 'media_url', None)
        if not media_url:
            raise ValueError("Clip does not have a media URL")

        # Determine media type from clip
        media_type = getattr(clip, 'media_type', 'video').lower()

        # Create media container based on type
        if media_type == 'image' or media_type == 'photo':
            container_id = await ig_api.create_image_container(
                ig_account_id=ig_account_id,
                image_url=media_url,
                caption=caption
            )
        elif media_type == 'video' or media_type == 'reel':
            # For videos, we need to create a container and wait for it to be ready
            container_id = await ig_api.create_video_container(
                ig_account_id=ig_account_id,
                video_url=media_url,
                caption=caption,
                media_type="REELS"  # Instagram prefers Reels format for videos
            )

            # Wait for video to be ready (check status)
            # In production, this should be handled by a background task
            max_attempts = 30
            for attempt in range(max_attempts):
                status_result = await ig_api.check_container_status(container_id)
                status_code = status_result.get("status_code")

                if status_code == "FINISHED":
                    break
                elif status_code == "ERROR":
                    raise InstagramGraphAPIError(f"Video processing failed: {status_result.get('status')}")

                # Wait before checking again
                await asyncio.sleep(2)

                if attempt == max_attempts - 1:
                    raise InstagramGraphAPIError("Video processing timeout")
        elif media_type == 'carousel':
            # Carousel: create child containers, then carousel container
            carousel_urls = getattr(clip, 'carousel_media_urls', [])
            carousel_types = getattr(clip, 'carousel_media_types', [])

            if not carousel_urls or len(carousel_urls) < 2:
                raise ValueError("Carousel requires at least 2 media items")

            if len(carousel_urls) > 10:
                raise ValueError("Carousel supports a maximum of 10 media items")

            # Create child containers (captions only on parent)
            children_ids = []
            for i, url in enumerate(carousel_urls):
                child_type = carousel_types[i] if i < len(carousel_types) else 'image'

                if child_type in ('image', 'photo'):
                    child_id = await ig_api.create_image_container(
                        ig_account_id=ig_account_id,
                        image_url=url,
                    )
                elif child_type == 'video':
                    child_id = await ig_api.create_video_container(
                        ig_account_id=ig_account_id,
                        video_url=url,
                    )
                    # Wait for video child to be ready
                    max_attempts = 30
                    for attempt in range(max_attempts):
                        status_result = await ig_api.check_container_status(child_id)
                        status_code = status_result.get("status_code")
                        if status_code == "FINISHED":
                            break
                        elif status_code == "ERROR":
                            raise InstagramGraphAPIError(
                                f"Carousel video processing failed: {status_result.get('status')}"
                            )
                        await asyncio.sleep(2)
                        if attempt == max_attempts - 1:
                            raise InstagramGraphAPIError("Carousel video processing timeout")
                else:
                    raise ValueError(f"Unsupported carousel child media type: {child_type}")

                children_ids.append(child_id)

            # Create carousel container with caption on the parent
            container_id = await ig_api.create_carousel_container(
                ig_account_id=ig_account_id,
                children=children_ids,
                caption=caption,
            )

        elif media_type == 'story':
            # Stories: determine if image or video story
            story_media_type = getattr(clip, 'story_media_type', 'IMAGE').upper()

            container_id = await ig_api.create_story_container(
                ig_account_id=ig_account_id,
                media_url=media_url,
                media_type=story_media_type,
            )

            # For video stories, wait for processing
            if story_media_type == "VIDEO":
                max_attempts = 30
                for attempt in range(max_attempts):
                    status_result = await ig_api.check_container_status(container_id)
                    status_code = status_result.get("status_code")
                    if status_code == "FINISHED":
                        break
                    elif status_code == "ERROR":
                        raise InstagramGraphAPIError(
                            f"Story video processing failed: {status_result.get('status')}"
                        )
                    await asyncio.sleep(2)
                    if attempt == max_attempts - 1:
                        raise InstagramGraphAPIError("Story video processing timeout")

        else:
            raise ValueError(f"Unsupported media type: {media_type}")

        # Publish the container
        media_id = await ig_api.publish_container(
            ig_account_id=ig_account_id,
            creation_id=container_id
        )

        # Get the permalink for the published media
        media_details = await ig_api.get_media_details(media_id)
        permalink = media_details.get("permalink", "")

        return {
            "platform_post_id": media_id,
            "platform_url": permalink
        }

    except InstagramGraphAPIError as e:
        logger.error(f"Instagram API error: {str(e)}")
        raise ValueError(f"Instagram API error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to publish to Instagram: {str(e)}")
        raise
    finally:
        await ig_api.close()


async def _publish_to_youtube(
    post: SocialPost,
    clip,
    account: Account,
) -> dict:
    """
    Publish a post to YouTube using Data API v3 with resumable uploads.

    Supports:
    - Standard video uploads
    - Shorts (vertical, < 60s — detected from clip metadata or title)

    Args:
        post: Social post object
        clip: Clip object containing media
        account: Connected YouTube account

    Returns:
        Dictionary with platform_post_id and platform_url
    """
    access_token = decrypt_token(account.access_token_enc)
    if not access_token:
        raise ValueError("Invalid YouTube access token")

    yt_api = create_youtube_service(access_token)

    try:
        # Prepare title and description
        title = post.title or "Untitled Video"
        description = post.caption or ""
        if post.hashtags:
            hashtags_list = json.loads(post.hashtags) if isinstance(post.hashtags, str) else post.hashtags
            description = f"{description}\n\n{' '.join(hashtags_list)}"

        tags = []
        if post.hashtags:
            hashtags_list = json.loads(post.hashtags) if isinstance(post.hashtags, str) else post.hashtags
            tags = [tag.lstrip("#") for tag in hashtags_list]

        # Determine if this is a Short based on clip properties
        is_short = False
        duration = getattr(clip, "duration", None)
        width = getattr(clip, "width", None)
        height = getattr(clip, "height", None)

        # Auto-detect Shorts: vertical video under 60 seconds
        if duration and duration <= 60:
            if height and width and height > width:
                is_short = True
        # Also check if user explicitly flagged it
        if "#Shorts" in title or "#Shorts" in description:
            is_short = True

        # Get the file path for the clip
        file_path = getattr(clip, "file_path", None)
        if not file_path:
            raise ValueError("Clip does not have a file path for upload")

        # Determine privacy status
        privacy_status = "public"
        if post.scheduled_for and post.scheduled_for > datetime.utcnow():
            privacy_status = "private"

        # Upload using the appropriate method
        if is_short:
            video_resource = await yt_api.upload_short(
                file_path=file_path,
                title=title,
                description=description,
                tags=tags,
                privacy_status=privacy_status,
            )
        else:
            video_resource = await yt_api.upload_video_file(
                file_path=file_path,
                title=title,
                description=description,
                tags=tags,
                privacy_status=privacy_status,
                is_short=False,
            )

        video_id = video_resource.get("id")
        if not video_id:
            raise ValueError("Upload succeeded but no video ID returned")

        platform_url = f"https://www.youtube.com/watch?v={video_id}"
        if is_short:
            platform_url = f"https://www.youtube.com/shorts/{video_id}"

        logger.info(f"Published YouTube {'Short' if is_short else 'video'}: {video_id}")

        return {
            "platform_post_id": video_id,
            "platform_url": platform_url,
        }

    except YouTubeAPIError as e:
        logger.error(f"YouTube API error: {str(e)}")
        raise ValueError(f"YouTube API error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to publish to YouTube: {str(e)}")
        raise
    finally:
        await yt_api.close()


async def _publish_to_tiktok(
    post: SocialPost,
    clip,
    account: Account,
) -> dict:
    """
    Publish a post to TikTok using the Content Posting API.

    Supports:
    - Video posts (via file upload or URL)
    - Photo posts (via URL)

    Args:
        post: Social post object
        clip: Clip object containing media
        account: Connected TikTok account

    Returns:
        Dictionary with platform_post_id and platform_url
    """
    access_token = decrypt_token(account.access_token_enc)
    if not access_token:
        raise ValueError("Invalid TikTok access token")

    tt_api = create_tiktok_service(access_token)

    try:
        # Prepare caption with hashtags
        caption = post.caption or ""
        if post.hashtags:
            hashtags_list = json.loads(post.hashtags) if isinstance(post.hashtags, str) else post.hashtags
            caption = f"{caption}\n\n{' '.join(hashtags_list)}"

        # Determine media type and publish accordingly
        media_type = getattr(clip, 'media_type', 'video').lower()
        file_path = getattr(clip, 'file_path', None)
        media_url = getattr(clip, 'media_url', None)

        if media_type in ('video', 'reel'):
            # Video post
            if file_path:
                result = await tt_api.upload_video_file(
                    file_path=file_path,
                    title=caption,
                    privacy_level="PUBLIC_TO_EVERYONE",
                )
            elif media_url:
                result = await tt_api.publish_video_by_url(
                    video_url=media_url,
                    title=caption,
                    privacy_level="PUBLIC_TO_EVERYONE",
                )
            else:
                raise ValueError("Clip does not have a file path or media URL")

            publish_id = result["publish_id"]

            # Wait for publishing to complete
            status_data = await tt_api.wait_for_publish(publish_id)
            created_items = status_data.get("created_items", [])

            platform_post_id = publish_id
            platform_url = f"https://www.tiktok.com/@user/video/{publish_id}"

            if created_items:
                item_id = created_items[0].get("id", publish_id)
                platform_post_id = item_id
                platform_url = f"https://www.tiktok.com/@user/video/{item_id}"

        elif media_type in ('image', 'photo'):
            # Photo post
            if not media_url:
                raise ValueError("Photo post requires a media URL")

            photo_urls = getattr(clip, 'carousel_media_urls', None) or [media_url]

            result = await tt_api.publish_photo_post(
                photo_urls=photo_urls,
                title=caption,
                privacy_level="PUBLIC_TO_EVERYONE",
            )

            publish_id = result["publish_id"]
            status_data = await tt_api.wait_for_publish(publish_id)
            created_items = status_data.get("created_items", [])

            platform_post_id = publish_id
            platform_url = f"https://www.tiktok.com/@user/photo/{publish_id}"

            if created_items:
                item_id = created_items[0].get("id", publish_id)
                platform_post_id = item_id
                platform_url = f"https://www.tiktok.com/@user/photo/{item_id}"

        else:
            raise ValueError(f"Unsupported media type for TikTok: {media_type}")

        logger.info(f"Published to TikTok: {platform_post_id}")

        return {
            "platform_post_id": platform_post_id,
            "platform_url": platform_url,
        }

    except TikTokAPIError as e:
        logger.error(f"TikTok API error: {str(e)}")
        raise ValueError(f"TikTok API error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to publish to TikTok: {str(e)}")
        raise
    finally:
        await tt_api.close()
