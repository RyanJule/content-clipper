"""
TikTok Content Posting API Service

Handles all TikTok API interactions for:
- Video post publishing (direct post and file upload)
- Photo post publishing (single and multi-image)
- Stories publishing

Uses TikTok's Content Posting API v2:
- https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class TikTokAPIError(Exception):
    """Custom exception for TikTok API errors"""
    pass


class TikTokAuthError(TikTokAPIError):
    """Raised when TikTok returns an authentication/authorization error.

    This typically means the access token is expired or invalid.
    The caller should refresh the token or prompt the user to reconnect.
    """
    pass


# TikTok error codes that indicate an invalid/expired access token
_TIKTOK_AUTH_ERROR_CODES = frozenset({
    "access_token_invalid",
    "access_token_expired",
    "token_not_authorized",
})


class TikTokService:
    """
    TikTok Content Posting API client.

    Scopes used:
    - user.info.basic: Get basic user info
    - user.info.stats: Get user stats (follower_count, following_count, etc.)
    - video.upload: Upload video content
    - video.publish: Publish video content
    """

    BASE_URL = "https://open.tiktokapis.com/v2"

    # TikTok video constraints
    MAX_VIDEO_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
    MIN_VIDEO_DURATION = 1  # 1 second
    MAX_VIDEO_DURATION = 600  # 10 minutes
    MAX_PHOTO_IMAGES = 35
    MIN_PHOTO_IMAGES = 1
    CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks for file upload

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, read=300.0),
            headers=self.headers,
        )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        data: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Make an API request to TikTok Content Posting API"""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = dict(self.headers)
        if extra_headers:
            headers.update(extra_headers)

        try:
            if method == "GET":
                response = await self.client.get(url, params=params, headers=headers)
            elif method == "POST":
                if data is not None:
                    response = await self.client.post(
                        url, content=data, headers=headers, params=params
                    )
                elif json_data is not None:
                    response = await self.client.post(
                        url, json=json_data, headers=headers, params=params
                    )
                else:
                    response = await self.client.post(url, headers=headers, params=params)
            elif method == "PUT":
                if data is not None:
                    response = await self.client.put(
                        url, content=data, headers=headers, params=params
                    )
                else:
                    response = await self.client.put(
                        url, json=json_data, headers=headers, params=params
                    )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            result = response.json()

            # TikTok API wraps errors in the response body
            error = result.get("error", {})
            if error.get("code") and error["code"] != "ok":
                error_msg = error.get("message", "Unknown TikTok API error")
                log_id = error.get("log_id", "")
                error_code = error["code"]
                full_msg = f"TikTok API error: {error_msg} (code: {error_code}, log_id: {log_id})"
                if error_code in _TIKTOK_AUTH_ERROR_CODES:
                    raise TikTokAuthError(full_msg)
                raise TikTokAPIError(full_msg)

            return result

        except httpx.HTTPStatusError as e:
            error_data = {}
            try:
                error_data = e.response.json()
            except Exception:
                pass
            error_info = error_data.get("error", {})
            error_msg = error_info.get("message", str(e))
            error_code = error_info.get("code", "")
            logger.error(f"TikTok API error ({e.response.status_code}): {error_msg}")
            if e.response.status_code == 401 or error_code in _TIKTOK_AUTH_ERROR_CODES:
                raise TikTokAuthError(f"TikTok API error: {error_msg}")
            raise TikTokAPIError(f"TikTok API error: {error_msg}")
        except httpx.TimeoutException:
            raise TikTokAPIError("TikTok API request timed out")
        except TikTokAPIError:
            raise
        except Exception as e:
            logger.error(f"TikTok request failed: {str(e)}")
            raise TikTokAPIError(f"Request failed: {str(e)}")

    # ==================== USER INFO ====================

    async def get_user_info(self) -> Dict[str, Any]:
        """
        Get the authenticated user's TikTok profile information.

        Returns:
            User info with open_id, display_name, avatar_url
        """
        result = await self._make_request(
            "GET",
            "user/info/",
            params={"fields": "open_id,display_name,avatar_url,follower_count,following_count,likes_count,video_count"},
        )
        return result.get("data", {}).get("user", {})

    # ==================== CREATOR INFO ====================

    async def query_creator_info(self) -> Dict[str, Any]:
        """
        Query creator info to get posting constraints.

        Required before publishing to understand:
        - Max video duration
        - Whether the creator can post comments
        - Privacy level options
        - etc.

        Returns:
            Creator info with privacy_level_options, max_video_post_duration_sec, etc.
        """
        result = await self._make_request(
            "POST",
            "post/publish/creator_info/query/",
        )
        return result.get("data", {})

    # ==================== VIDEO PUBLISHING (Inbox Upload) ====================

    async def publish_video_by_url(
        self,
        video_url: str,
        title: str = "",
        privacy_level: str = "SELF_ONLY",
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        video_cover_timestamp_ms: int = 0,
        brand_content_toggle: bool = False,
        brand_organic_toggle: bool = False,
    ) -> Dict[str, Any]:
        """
        Upload a video to the user's TikTok inbox using a publicly accessible URL.

        The video will be pulled from the URL by TikTok's servers and placed
        in the user's TikTok inbox. The user must open TikTok to finalize
        and publish the video (set caption, privacy, etc.).

        Uses the inbox endpoint (/post/publish/inbox/video/init/) which only
        accepts source_info. Post metadata (title, privacy, etc.) is set by
        the user in the TikTok app.

        Args:
            video_url: Publicly accessible URL of the video
            title: Unused (kept for backward compatibility)
            privacy_level: Unused (kept for backward compatibility)
            disable_duet: Unused (kept for backward compatibility)
            disable_comment: Unused (kept for backward compatibility)
            disable_stitch: Unused (kept for backward compatibility)
            video_cover_timestamp_ms: Unused (kept for backward compatibility)
            brand_content_toggle: Unused (kept for backward compatibility)
            brand_organic_toggle: Unused (kept for backward compatibility)

        Returns:
            Publish ID for status tracking
        """
        body = {
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": video_url,
            },
        }

        result = await self._make_request(
            "POST",
            "post/publish/inbox/video/init/",
            json_data=body,
        )

        publish_id = result.get("data", {}).get("publish_id")
        if not publish_id:
            raise TikTokAPIError("No publish_id returned from video init")

        logger.info(f"Initiated TikTok video inbox upload (URL): {publish_id}")
        return {"publish_id": publish_id}

    # ==================== VIDEO PUBLISHING (File Upload) ====================

    async def init_video_upload(
        self,
        video_size: int,
        chunk_size: Optional[int] = None,
        title: str = "",
        privacy_level: str = "SELF_ONLY",
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        video_cover_timestamp_ms: int = 0,
        brand_content_toggle: bool = False,
        brand_organic_toggle: bool = False,
    ) -> Dict[str, Any]:
        """
        Initialize a file-based video upload to the user's TikTok inbox.

        Uses the inbox endpoint which only accepts source_info.
        The user finalizes post details in the TikTok app.

        For videos > 64MB, uses chunked upload. For smaller videos, uses single upload.

        Args:
            video_size: Total video file size in bytes
            chunk_size: Size of each chunk (for chunked uploads)
            title: Unused (kept for backward compatibility)
            privacy_level: Unused (kept for backward compatibility)
            disable_duet: Unused (kept for backward compatibility)
            disable_comment: Unused (kept for backward compatibility)
            disable_stitch: Unused (kept for backward compatibility)
            video_cover_timestamp_ms: Unused (kept for backward compatibility)
            brand_content_toggle: Unused (kept for backward compatibility)
            brand_organic_toggle: Unused (kept for backward compatibility)

        Returns:
            Upload URL and publish_id
        """
        # Use chunked upload for large files (> 64MB), single chunk for small files
        if video_size > 64 * 1024 * 1024:
            actual_chunk_size = chunk_size or self.CHUNK_SIZE
            total_chunk_count = -(-video_size // actual_chunk_size)  # ceiling division
        else:
            actual_chunk_size = video_size
            total_chunk_count = 1

        source_info = {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": actual_chunk_size,
            "total_chunk_count": total_chunk_count,
        }

        body = {
            "source_info": source_info,
        }

        result = await self._make_request(
            "POST",
            "post/publish/inbox/video/init/",
            json_data=body,
        )

        data = result.get("data", {})
        publish_id = data.get("publish_id")
        upload_url = data.get("upload_url")

        if not publish_id or not upload_url:
            raise TikTokAPIError("Failed to initialize video upload: missing publish_id or upload_url")

        logger.info(f"Initialized TikTok inbox video upload: {publish_id}")
        return {
            "publish_id": publish_id,
            "upload_url": upload_url,
        }

    async def upload_video_bytes(
        self,
        video_data: bytes,
        title: str = "",
        privacy_level: str = "SELF_ONLY",
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        video_cover_timestamp_ms: int = 0,
        on_progress: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Upload a video from bytes data.

        Handles both single-part and chunked uploads based on file size.

        Args:
            video_data: Video file bytes
            title: Video caption
            privacy_level: Privacy level
            disable_duet: Disable duet
            disable_comment: Disable comments
            disable_stitch: Disable stitch
            video_cover_timestamp_ms: Cover timestamp
            on_progress: Callback(bytes_uploaded, total_bytes)

        Returns:
            Dictionary with publish_id
        """
        video_size = len(video_data)

        if video_size > self.MAX_VIDEO_SIZE:
            raise TikTokAPIError(f"Video file exceeds maximum size of {self.MAX_VIDEO_SIZE} bytes")

        # Initialize upload
        init_result = await self.init_video_upload(
            video_size=video_size,
            title=title,
            privacy_level=privacy_level,
            disable_duet=disable_duet,
            disable_comment=disable_comment,
            disable_stitch=disable_stitch,
            video_cover_timestamp_ms=video_cover_timestamp_ms,
        )

        upload_url = init_result["upload_url"]
        publish_id = init_result["publish_id"]

        if video_size <= 64 * 1024 * 1024:
            # Single upload for small files
            headers = {
                "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
                "Content-Type": "video/mp4",
            }
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=600.0)) as client:
                response = await client.put(
                    upload_url,
                    content=video_data,
                    headers=headers,
                )
                response.raise_for_status()

            if on_progress:
                on_progress(video_size, video_size)
        else:
            # Chunked upload for large files
            bytes_uploaded = 0
            chunk_size = self.CHUNK_SIZE

            while bytes_uploaded < video_size:
                chunk_end = min(bytes_uploaded + chunk_size, video_size)
                chunk = video_data[bytes_uploaded:chunk_end]

                headers = {
                    "Content-Range": f"bytes {bytes_uploaded}-{chunk_end - 1}/{video_size}",
                    "Content-Type": "video/mp4",
                }

                async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=300.0)) as client:
                    response = await client.put(
                        upload_url,
                        content=chunk,
                        headers=headers,
                    )
                    response.raise_for_status()

                bytes_uploaded = chunk_end

                if on_progress:
                    on_progress(bytes_uploaded, video_size)

        logger.info(f"Video upload complete for publish_id: {publish_id}")
        return {"publish_id": publish_id}

    async def upload_video_file(
        self,
        file_path: str,
        title: str = "",
        privacy_level: str = "SELF_ONLY",
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        video_cover_timestamp_ms: int = 0,
        on_progress: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Upload a video from a file path.

        Args:
            file_path: Path to the video file
            title: Video caption
            privacy_level: Privacy level
            disable_duet: Disable duet
            disable_comment: Disable comments
            disable_stitch: Disable stitch
            video_cover_timestamp_ms: Cover timestamp
            on_progress: Callback(bytes_uploaded, total_bytes)

        Returns:
            Dictionary with publish_id
        """
        video_size = os.path.getsize(file_path)

        if video_size > self.MAX_VIDEO_SIZE:
            raise TikTokAPIError(f"Video file exceeds maximum size of {self.MAX_VIDEO_SIZE} bytes")

        # Initialize upload
        init_result = await self.init_video_upload(
            video_size=video_size,
            title=title,
            privacy_level=privacy_level,
            disable_duet=disable_duet,
            disable_comment=disable_comment,
            disable_stitch=disable_stitch,
            video_cover_timestamp_ms=video_cover_timestamp_ms,
        )

        upload_url = init_result["upload_url"]
        publish_id = init_result["publish_id"]

        bytes_uploaded = 0
        chunk_size = self.CHUNK_SIZE

        with open(file_path, "rb") as f:
            while bytes_uploaded < video_size:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                chunk_end = bytes_uploaded + len(chunk)
                headers = {
                    "Content-Range": f"bytes {bytes_uploaded}-{chunk_end - 1}/{video_size}",
                    "Content-Type": "video/mp4",
                }

                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=300.0)) as client:
                            response = await client.put(
                                upload_url,
                                content=chunk,
                                headers=headers,
                            )
                            response.raise_for_status()
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise TikTokAPIError(f"Chunk upload failed after {max_retries} retries: {e}")
                        wait_time = 2 ** (attempt + 1)
                        logger.warning(f"Chunk upload retry {attempt + 1}/{max_retries}, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)

                bytes_uploaded = chunk_end

                if on_progress:
                    on_progress(bytes_uploaded, video_size)

        logger.info(f"Video file upload complete for publish_id: {publish_id}")
        return {"publish_id": publish_id}

    # ==================== PHOTO POST PUBLISHING ====================

    async def publish_photo_post(
        self,
        photo_urls: List[str],
        title: str = "",
        privacy_level: str = "SELF_ONLY",
        disable_comment: bool = False,
        auto_add_music: bool = True,
        brand_content_toggle: bool = False,
        brand_organic_toggle: bool = False,
    ) -> Dict[str, Any]:
        """
        Publish a photo post (carousel of images).

        TikTok photo posts support 1-35 images.

        Args:
            photo_urls: List of publicly accessible image URLs (1-35)
            title: Post description/caption (max 2200 chars)
            privacy_level: SELF_ONLY, MUTUAL_FOLLOW_FRIENDS, FOLLOWER_OF_CREATOR, or PUBLIC_TO_EVERYONE
            disable_comment: Disable comments
            auto_add_music: Auto-add background music
            brand_content_toggle: Branded content flag
            brand_organic_toggle: Organic branded content flag

        Returns:
            Publish ID for status tracking
        """
        if not photo_urls:
            raise TikTokAPIError("At least one photo URL is required")

        if len(photo_urls) > self.MAX_PHOTO_IMAGES:
            raise TikTokAPIError(f"Maximum {self.MAX_PHOTO_IMAGES} images allowed per photo post")

        post_info = {
            "title": title[:2200],
            "privacy_level": privacy_level,
            "disable_comment": disable_comment,
            "auto_add_music": auto_add_music,
            "brand_content_toggle": brand_content_toggle,
            "brand_organic_toggle": brand_organic_toggle,
        }

        body = {
            "post_info": post_info,
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_cover_index": 0,
                "photo_images": photo_urls,
            },
            "post_mode": "DIRECT_POST",
            "media_type": "PHOTO",
        }

        result = await self._make_request(
            "POST",
            "post/publish/content/init/",
            json_data=body,
        )

        publish_id = result.get("data", {}).get("publish_id")
        if not publish_id:
            raise TikTokAPIError("No publish_id returned from photo post init")

        logger.info(f"Initiated TikTok photo post: {publish_id}")
        return {"publish_id": publish_id}

    # ==================== STORIES PUBLISHING ====================

    async def publish_story_by_url(
        self,
        media_url: str,
        media_type: str = "VIDEO",
    ) -> Dict[str, Any]:
        """
        Publish a story using a publicly accessible URL.

        Stories are visible for 24 hours.

        Args:
            media_url: Publicly accessible URL of the media (video or image)
            media_type: "VIDEO" or "PHOTO"

        Returns:
            Publish ID for status tracking
        """
        post_info = {
            "privacy_level": "STORY_PRIVACY",
        }

        if media_type.upper() == "PHOTO":
            source_info = {
                "source": "PULL_FROM_URL",
                "photo_images": [media_url],
                "photo_cover_index": 0,
            }
        else:
            source_info = {
                "source": "PULL_FROM_URL",
                "video_url": media_url,
            }

        if media_type.upper() == "PHOTO":
            body = {
                "post_info": post_info,
                "source_info": source_info,
                "post_mode": "DIRECT_POST",
                "media_type": "PHOTO",
            }
            endpoint = "post/publish/content/init/"
        else:
            body = {
                "source_info": source_info,
            }
            endpoint = "post/publish/inbox/video/init/"

        result = await self._make_request(
            "POST",
            endpoint,
            json_data=body,
        )

        publish_id = result.get("data", {}).get("publish_id")
        if not publish_id:
            raise TikTokAPIError("No publish_id returned from story init")

        logger.info(f"Initiated TikTok story publish: {publish_id}")
        return {"publish_id": publish_id}

    async def init_story_video_upload(
        self,
        video_size: int,
    ) -> Dict[str, Any]:
        """
        Initialize a file-based story video upload to the user's TikTok inbox.

        Uses the inbox endpoint. The user finalizes the story in the TikTok app.

        Args:
            video_size: Total video file size in bytes

        Returns:
            Upload URL and publish_id
        """
        source_info = {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
        }

        if video_size > 64 * 1024 * 1024:
            chunk_size = self.CHUNK_SIZE
            total_chunk_count = -(-video_size // chunk_size)
            source_info["chunk_size"] = chunk_size
            source_info["total_chunk_count"] = total_chunk_count

        body = {
            "source_info": source_info,
        }

        result = await self._make_request(
            "POST",
            "post/publish/inbox/video/init/",
            json_data=body,
        )

        data = result.get("data", {})
        publish_id = data.get("publish_id")
        upload_url = data.get("upload_url")

        if not publish_id or not upload_url:
            raise TikTokAPIError("Failed to initialize story upload")

        logger.info(f"Initialized TikTok story video upload: {publish_id}")
        return {
            "publish_id": publish_id,
            "upload_url": upload_url,
        }

    async def upload_story_video_bytes(
        self,
        video_data: bytes,
        on_progress: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Upload a story video from bytes.

        Args:
            video_data: Video file bytes
            on_progress: Callback(bytes_uploaded, total_bytes)

        Returns:
            Dictionary with publish_id
        """
        video_size = len(video_data)

        init_result = await self.init_story_video_upload(video_size=video_size)
        upload_url = init_result["upload_url"]
        publish_id = init_result["publish_id"]

        # Upload video data
        headers = {
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
            "Content-Type": "video/mp4",
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=600.0)) as client:
            response = await client.put(
                upload_url,
                content=video_data,
                headers=headers,
            )
            response.raise_for_status()

        if on_progress:
            on_progress(video_size, video_size)

        logger.info(f"Story video upload complete: {publish_id}")
        return {"publish_id": publish_id}

    # ==================== PUBLISH STATUS ====================

    async def get_publish_status(self, publish_id: str) -> Dict[str, Any]:
        """
        Check the status of a publish operation.

        Status values:
        - PROCESSING_UPLOAD: Upload in progress
        - PROCESSING_DOWNLOAD: TikTok downloading from URL
        - SEND_TO_USER_INBOX: Awaiting user confirmation
        - PUBLISH_COMPLETE: Successfully published
        - FAILED: Publish failed

        Args:
            publish_id: The publish_id from init response

        Returns:
            Status information including status, created_items, etc.
        """
        body = {
            "publish_id": publish_id,
        }

        result = await self._make_request(
            "POST",
            "post/publish/status/fetch/",
            json_data=body,
        )

        return result.get("data", {})

    async def wait_for_publish(
        self,
        publish_id: str,
        max_attempts: int = 30,
        poll_interval: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Wait for a publish operation to complete.

        Polls the status endpoint until the publish is complete or fails.

        Args:
            publish_id: The publish_id to check
            max_attempts: Maximum number of status checks
            poll_interval: Seconds between checks

        Returns:
            Final status data with publish result
        """
        for attempt in range(max_attempts):
            status_data = await self.get_publish_status(publish_id)
            status = status_data.get("status")

            if status == "PUBLISH_COMPLETE":
                logger.info(f"TikTok publish complete: {publish_id}")
                return status_data

            if status == "SEND_TO_USER_INBOX":
                logger.info(f"TikTok video sent to user inbox: {publish_id}")
                return status_data

            if status == "FAILED":
                fail_reason = status_data.get("fail_reason", "Unknown")
                raise TikTokAPIError(
                    f"TikTok publish failed: {fail_reason}"
                )

            logger.debug(
                f"TikTok publish status ({attempt + 1}/{max_attempts}): {status}"
            )
            await asyncio.sleep(poll_interval)

        raise TikTokAPIError(
            f"TikTok publish timed out after {max_attempts} attempts for publish_id: {publish_id}"
        )


def create_tiktok_service(access_token: str) -> TikTokService:
    """
    Create a TikTok API service instance.

    Args:
        access_token: OAuth2 access token with TikTok scopes

    Returns:
        TikTokService instance
    """
    return TikTokService(access_token)
