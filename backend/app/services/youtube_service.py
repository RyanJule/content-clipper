"""
YouTube Data API v3 Service

Handles all YouTube API interactions for:
- Video uploads (standard and resumable)
- Shorts publishing (vertical, < 60s)
- Community posts
- Thumbnail management
- Channel information
- Video management
"""

import asyncio
import io
import json
import logging
import math
import os
from typing import Any, BinaryIO, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors"""
    pass


class YouTubeService:
    """
    YouTube Data API v3 client.

    Scopes used:
    - youtube.upload: Upload videos
    - youtube: Manage account (community posts, playlists)
    - youtube.readonly: Read channel info, videos, analytics
    - youtube.force-ssl: Required for comments/community posts
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3"

    # Resumable upload chunk size (5 MB - minimum for YouTube)
    CHUNK_SIZE = 5 * 1024 * 1024

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
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
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[bytes] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make an API request to YouTube Data API"""
        headers = dict(self.headers)
        if extra_headers:
            headers.update(extra_headers)

        try:
            if method == "GET":
                response = await self.client.get(url, params=params, headers=headers)
            elif method == "POST":
                if data is not None:
                    response = await self.client.post(
                        url, params=params, content=data, headers=headers
                    )
                elif json_data is not None:
                    response = await self.client.post(
                        url, params=params, json=json_data, headers=headers
                    )
                else:
                    response = await self.client.post(url, params=params, headers=headers)
            elif method == "PUT":
                if data is not None:
                    response = await self.client.put(
                        url, params=params, content=data, headers=headers
                    )
                elif json_data is not None:
                    response = await self.client.put(
                        url, params=params, json=json_data, headers=headers
                    )
                else:
                    response = await self.client.put(url, params=params, headers=headers)
            elif method == "DELETE":
                response = await self.client.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            if response.status_code == 204:
                return {"success": True}

            return response.json()

        except httpx.HTTPStatusError as e:
            error_data = {}
            try:
                error_data = e.response.json()
            except Exception:
                pass
            error_msg = (
                error_data.get("error", {}).get("message", "")
                or str(e)
            )
            logger.error(f"YouTube API error ({e.response.status_code}): {error_msg}")
            raise YouTubeAPIError(f"YouTube API error: {error_msg}")
        except httpx.TimeoutException:
            raise YouTubeAPIError("YouTube API request timed out")
        except Exception as e:
            logger.error(f"YouTube request failed: {str(e)}")
            raise YouTubeAPIError(f"Request failed: {str(e)}")

    # ==================== CHANNEL INFO ====================

    async def get_channel_info(self) -> Dict[str, Any]:
        """
        Get the authenticated user's YouTube channel information.

        Returns:
            Channel info with snippet, statistics, and content details
        """
        params = {
            "part": "snippet,statistics,contentDetails,brandingSettings",
            "mine": "true",
        }
        data = await self._make_request("GET", f"{self.BASE_URL}/channels", params=params)
        items = data.get("items", [])
        if not items:
            raise YouTubeAPIError("No YouTube channel found")
        return items[0]

    async def get_channel_videos(
        self,
        max_results: int = 25,
        page_token: Optional[str] = None,
        order: str = "date",
    ) -> Dict[str, Any]:
        """
        Get videos from the authenticated user's channel.

        Args:
            max_results: Maximum number of results (1-50)
            page_token: Token for pagination
            order: Sort order (date, rating, relevance, title, viewCount)

        Returns:
            Search result list with video details
        """
        params = {
            "part": "snippet",
            "forMine": "true",
            "type": "video",
            "maxResults": min(max_results, 50),
            "order": order,
        }
        if page_token:
            params["pageToken"] = page_token

        search_data = await self._make_request(
            "GET", f"{self.BASE_URL}/search", params=params
        )

        # Get full video details for the found videos
        video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]
        if video_ids:
            video_params = {
                "part": "snippet,contentDetails,statistics,status",
                "id": ",".join(video_ids),
            }
            video_data = await self._make_request(
                "GET", f"{self.BASE_URL}/videos", params=video_params
            )
            return {
                "items": video_data.get("items", []),
                "pageInfo": search_data.get("pageInfo", {}),
                "nextPageToken": search_data.get("nextPageToken"),
                "prevPageToken": search_data.get("prevPageToken"),
            }

        return {
            "items": [],
            "pageInfo": search_data.get("pageInfo", {}),
        }

    async def get_video_details(self, video_id: str) -> Dict[str, Any]:
        """
        Get details for a specific video.

        Args:
            video_id: YouTube video ID

        Returns:
            Video resource with all parts
        """
        params = {
            "part": "snippet,contentDetails,statistics,status,player",
            "id": video_id,
        }
        data = await self._make_request("GET", f"{self.BASE_URL}/videos", params=params)
        items = data.get("items", [])
        if not items:
            raise YouTubeAPIError(f"Video {video_id} not found")
        return items[0]

    # ==================== VIDEO UPLOAD (RESUMABLE) ====================

    async def initiate_resumable_upload(
        self,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        category_id: str = "22",
        privacy_status: str = "private",
        is_short: bool = False,
        scheduled_start_time: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        notify_subscribers: bool = True,
    ) -> str:
        """
        Initiate a resumable video upload session.

        Args:
            title: Video title (max 100 chars)
            description: Video description (max 5000 chars)
            tags: List of video tags
            category_id: YouTube category ID (22 = People & Blogs)
            privacy_status: "private", "public", or "unlisted"
            is_short: If True, marks video as a YouTube Short
            scheduled_start_time: ISO 8601 datetime for scheduled publish
            thumbnail_url: URL for custom thumbnail (set after upload)
            notify_subscribers: Whether to notify subscribers

        Returns:
            Upload URI for resumable upload
        """
        # Build video resource
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        if tags:
            body["snippet"]["tags"] = tags[:500]

        if is_short:
            # Shorts are indicated by #Shorts in title or description
            if "#Shorts" not in title and "#Shorts" not in description:
                body["snippet"]["title"] = f"{title[:92]} #Shorts"

        if scheduled_start_time and privacy_status == "private":
            body["status"]["privacyStatus"] = "private"
            body["status"]["publishAt"] = scheduled_start_time

        if not notify_subscribers:
            body["status"]["selfDeclaredMadeForKids"] = False

        # Initiate resumable upload
        url = f"{self.UPLOAD_URL}/videos"
        params = {
            "uploadType": "resumable",
            "part": "snippet,status",
        }

        if not notify_subscribers:
            params["notifySubscribers"] = "false"

        headers = {
            **self.headers,
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/*",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                params=params,
                json=body,
                headers=headers,
            )
            response.raise_for_status()

        upload_url = response.headers.get("Location")
        if not upload_url:
            raise YouTubeAPIError("Failed to get resumable upload URL")

        logger.info(f"Initiated resumable upload for '{title}'")
        return upload_url

    async def upload_video_chunk(
        self,
        upload_url: str,
        chunk_data: bytes,
        chunk_start: int,
        total_size: int,
    ) -> Dict[str, Any]:
        """
        Upload a chunk of video data via resumable upload.

        Args:
            upload_url: The resumable upload URI
            chunk_data: Bytes of the video chunk
            chunk_start: Start byte offset
            total_size: Total file size in bytes

        Returns:
            Response data (video resource if upload is complete)
        """
        chunk_end = chunk_start + len(chunk_data) - 1
        headers = {
            "Content-Length": str(len(chunk_data)),
            "Content-Range": f"bytes {chunk_start}-{chunk_end}/{total_size}",
            "Content-Type": "video/*",
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=300.0)) as client:
            response = await client.put(
                upload_url,
                content=chunk_data,
                headers=headers,
            )

        if response.status_code == 200 or response.status_code == 201:
            # Upload complete
            return {"complete": True, "video": response.json()}
        elif response.status_code == 308:
            # Upload incomplete, more chunks needed
            range_header = response.headers.get("Range", "")
            return {"complete": False, "range": range_header}
        else:
            error_text = response.text
            raise YouTubeAPIError(
                f"Chunk upload failed ({response.status_code}): {error_text}"
            )

    async def upload_video_file(
        self,
        file_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        category_id: str = "22",
        privacy_status: str = "private",
        is_short: bool = False,
        scheduled_start_time: Optional[str] = None,
        notify_subscribers: bool = True,
        on_progress: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Upload a complete video file using resumable uploads.

        Args:
            file_path: Path to the video file
            title: Video title
            description: Video description
            tags: Video tags
            category_id: YouTube category ID
            privacy_status: Privacy status
            is_short: Whether this is a YouTube Short
            scheduled_start_time: ISO 8601 datetime for scheduled publish
            notify_subscribers: Whether to notify subscribers
            on_progress: Callback(bytes_uploaded, total_bytes) for progress

        Returns:
            Video resource from YouTube API
        """
        file_size = os.path.getsize(file_path)

        # Initiate resumable upload
        upload_url = await self.initiate_resumable_upload(
            title=title,
            description=description,
            tags=tags,
            category_id=category_id,
            privacy_status=privacy_status,
            is_short=is_short,
            scheduled_start_time=scheduled_start_time,
            notify_subscribers=notify_subscribers,
        )

        # Upload in chunks
        bytes_uploaded = 0
        max_retries = 5

        with open(file_path, "rb") as f:
            while bytes_uploaded < file_size:
                chunk = f.read(self.CHUNK_SIZE)
                if not chunk:
                    break

                retries = 0
                while retries < max_retries:
                    try:
                        result = await self.upload_video_chunk(
                            upload_url=upload_url,
                            chunk_data=chunk,
                            chunk_start=bytes_uploaded,
                            total_size=file_size,
                        )

                        bytes_uploaded += len(chunk)

                        if on_progress:
                            on_progress(bytes_uploaded, file_size)

                        if result.get("complete"):
                            logger.info(f"Video upload complete: {title}")
                            return result["video"]

                        break  # Chunk succeeded, move to next
                    except YouTubeAPIError as e:
                        retries += 1
                        if retries >= max_retries:
                            raise YouTubeAPIError(
                                f"Upload failed after {max_retries} retries: {e}"
                            )
                        wait_time = min(2 ** retries, 16)
                        logger.warning(
                            f"Chunk upload retry {retries}/{max_retries}, "
                            f"waiting {wait_time}s: {e}"
                        )
                        await asyncio.sleep(wait_time)

        raise YouTubeAPIError("Upload did not complete properly")

    async def upload_video_bytes(
        self,
        video_data: bytes,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        category_id: str = "22",
        privacy_status: str = "private",
        is_short: bool = False,
        scheduled_start_time: Optional[str] = None,
        notify_subscribers: bool = True,
        on_progress: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Upload video from bytes using resumable uploads.

        Args:
            video_data: Video file bytes
            title: Video title
            description: Video description
            tags: Video tags
            category_id: YouTube category ID
            privacy_status: Privacy status
            is_short: Whether this is a YouTube Short
            scheduled_start_time: ISO 8601 for scheduled publish
            notify_subscribers: Whether to notify subscribers
            on_progress: Callback(bytes_uploaded, total_bytes)

        Returns:
            Video resource from YouTube API
        """
        total_size = len(video_data)

        upload_url = await self.initiate_resumable_upload(
            title=title,
            description=description,
            tags=tags,
            category_id=category_id,
            privacy_status=privacy_status,
            is_short=is_short,
            scheduled_start_time=scheduled_start_time,
            notify_subscribers=notify_subscribers,
        )

        bytes_uploaded = 0
        max_retries = 5

        while bytes_uploaded < total_size:
            chunk_end = min(bytes_uploaded + self.CHUNK_SIZE, total_size)
            chunk = video_data[bytes_uploaded:chunk_end]

            retries = 0
            while retries < max_retries:
                try:
                    result = await self.upload_video_chunk(
                        upload_url=upload_url,
                        chunk_data=chunk,
                        chunk_start=bytes_uploaded,
                        total_size=total_size,
                    )

                    bytes_uploaded += len(chunk)

                    if on_progress:
                        on_progress(bytes_uploaded, total_size)

                    if result.get("complete"):
                        logger.info(f"Video upload complete: {title}")
                        return result["video"]

                    break
                except YouTubeAPIError as e:
                    retries += 1
                    if retries >= max_retries:
                        raise YouTubeAPIError(
                            f"Upload failed after {max_retries} retries: {e}"
                        )
                    wait_time = min(2 ** retries, 16)
                    logger.warning(
                        f"Chunk upload retry {retries}/{max_retries}, "
                        f"waiting {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)

        raise YouTubeAPIError("Upload did not complete properly")

    # ==================== SHORTS PUBLISHING ====================

    async def upload_short(
        self,
        file_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        privacy_status: str = "public",
        notify_subscribers: bool = True,
        on_progress: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Upload a YouTube Short (vertical video, < 60 seconds).

        Shorts requirements:
        - Vertical format (9:16 aspect ratio, e.g. 1080x1920)
        - Max 60 seconds duration
        - #Shorts in title or description

        Args:
            file_path: Path to the short video file
            title: Video title (will append #Shorts if not present)
            description: Video description
            tags: Video tags
            privacy_status: Privacy status
            notify_subscribers: Whether to notify subscribers
            on_progress: Progress callback

        Returns:
            Video resource from YouTube API
        """
        if tags is None:
            tags = []
        if "Shorts" not in tags:
            tags.append("Shorts")

        return await self.upload_video_file(
            file_path=file_path,
            title=title,
            description=description,
            tags=tags,
            category_id="22",
            privacy_status=privacy_status,
            is_short=True,
            notify_subscribers=notify_subscribers,
            on_progress=on_progress,
        )

    async def upload_short_bytes(
        self,
        video_data: bytes,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        privacy_status: str = "public",
        notify_subscribers: bool = True,
        on_progress: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Upload a YouTube Short from bytes.

        Args:
            video_data: Video file bytes
            title: Video title
            description: Video description
            tags: Video tags
            privacy_status: Privacy status
            notify_subscribers: Whether to notify subscribers
            on_progress: Progress callback

        Returns:
            Video resource from YouTube API
        """
        if tags is None:
            tags = []
        if "Shorts" not in tags:
            tags.append("Shorts")

        return await self.upload_video_bytes(
            video_data=video_data,
            title=title,
            description=description,
            tags=tags,
            category_id="22",
            privacy_status=privacy_status,
            is_short=True,
            notify_subscribers=notify_subscribers,
            on_progress=on_progress,
        )

    # ==================== THUMBNAIL MANAGEMENT ====================

    async def set_thumbnail(
        self,
        video_id: str,
        image_data: bytes,
        content_type: str = "image/png",
    ) -> Dict[str, Any]:
        """
        Set a custom thumbnail for a video.

        Requirements:
        - Image must be 1280x720 (16:9)
        - Max file size: 2MB
        - Formats: JPG, GIF, PNG
        - Account must be verified for custom thumbnails

        Args:
            video_id: YouTube video ID
            image_data: Thumbnail image bytes
            content_type: MIME type of the image

        Returns:
            Thumbnail resource
        """
        url = f"{self.UPLOAD_URL}/thumbnails/set"
        params = {
            "videoId": video_id,
            "uploadType": "media",
        }
        headers = {
            **self.headers,
            "Content-Type": content_type,
            "Content-Length": str(len(image_data)),
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                params=params,
                content=image_data,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"Set thumbnail for video {video_id}")
        return result

    async def set_thumbnail_from_file(
        self,
        video_id: str,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Set a custom thumbnail from a file path.

        Args:
            video_id: YouTube video ID
            file_path: Path to the thumbnail image

        Returns:
            Thumbnail resource
        """
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
        }
        content_type = content_types.get(ext, "image/png")

        with open(file_path, "rb") as f:
            image_data = f.read()

        return await self.set_thumbnail(video_id, image_data, content_type)

    # ==================== COMMUNITY POSTS ====================

    async def create_community_post(
        self,
        text: str,
        image_data: Optional[bytes] = None,
        image_content_type: str = "image/png",
    ) -> Dict[str, Any]:
        """
        Create a YouTube community post.

        Note: The YouTube Data API has limited community post support.
        This uses the activities endpoint and may require specific channel
        eligibility (1000+ subscribers for community tab).

        Args:
            text: Post text content
            image_data: Optional image bytes to attach
            image_content_type: MIME type of the image

        Returns:
            Activity/post resource
        """
        # YouTube Data API v3 doesn't have a direct community posts endpoint.
        # Community posts are created via the channelBulletins insert method
        # through the activities API.
        body = {
            "snippet": {
                "description": text,
            },
        }

        # For text-only posts, use the bulletin type
        params = {
            "part": "snippet",
        }

        try:
            result = await self._make_request(
                "POST",
                f"{self.BASE_URL}/activities",
                params=params,
                json_data=body,
            )
            logger.info("Created community post")
            return result
        except YouTubeAPIError as e:
            # If activities API fails, provide guidance
            if "forbidden" in str(e).lower() or "403" in str(e):
                raise YouTubeAPIError(
                    "Community posts require a channel with 500+ subscribers "
                    "and the Community tab enabled. "
                    "Error: " + str(e)
                )
            raise

    # ==================== VIDEO MANAGEMENT ====================

    async def update_video(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category_id: Optional[str] = None,
        privacy_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update video metadata.

        Args:
            video_id: YouTube video ID
            title: New title (optional)
            description: New description (optional)
            tags: New tags (optional)
            category_id: New category (optional)
            privacy_status: New privacy status (optional)

        Returns:
            Updated video resource
        """
        # First get current video details
        current = await self.get_video_details(video_id)

        body = {
            "id": video_id,
            "snippet": current.get("snippet", {}),
        }

        parts = ["snippet"]

        if title is not None:
            body["snippet"]["title"] = title[:100]
        if description is not None:
            body["snippet"]["description"] = description[:5000]
        if tags is not None:
            body["snippet"]["tags"] = tags[:500]
        if category_id is not None:
            body["snippet"]["categoryId"] = category_id

        if privacy_status is not None:
            body["status"] = {"privacyStatus": privacy_status}
            parts.append("status")

        params = {"part": ",".join(parts)}

        result = await self._make_request(
            "PUT",
            f"{self.BASE_URL}/videos",
            params=params,
            json_data=body,
        )
        logger.info(f"Updated video {video_id}")
        return result

    async def delete_video(self, video_id: str) -> bool:
        """
        Delete a video.

        Args:
            video_id: YouTube video ID

        Returns:
            True if successful
        """
        params = {"id": video_id}
        await self._make_request(
            "DELETE", f"{self.BASE_URL}/videos", params=params
        )
        logger.info(f"Deleted video {video_id}")
        return True

    # ==================== COMMENTS ====================

    async def get_video_comments(
        self,
        video_id: str,
        max_results: int = 20,
        order: str = "relevance",
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get comment threads for a video.

        Args:
            video_id: YouTube video ID
            max_results: Max results (1-100)
            order: Sort order (time, relevance)
            page_token: Pagination token

        Returns:
            Comment thread list
        """
        params = {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": min(max_results, 100),
            "order": order,
            "textFormat": "plainText",
        }
        if page_token:
            params["pageToken"] = page_token

        return await self._make_request(
            "GET", f"{self.BASE_URL}/commentThreads", params=params
        )

    async def post_comment(
        self, video_id: str, text: str
    ) -> Dict[str, Any]:
        """
        Post a top-level comment on a video.

        Args:
            video_id: YouTube video ID
            text: Comment text

        Returns:
            Comment thread resource
        """
        body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": text,
                    }
                },
            }
        }

        return await self._make_request(
            "POST",
            f"{self.BASE_URL}/commentThreads",
            params={"part": "snippet"},
            json_data=body,
        )

    async def reply_to_comment(
        self, parent_id: str, text: str
    ) -> Dict[str, Any]:
        """
        Reply to a comment.

        Args:
            parent_id: Parent comment ID
            text: Reply text

        Returns:
            Comment resource
        """
        body = {
            "snippet": {
                "parentId": parent_id,
                "textOriginal": text,
            }
        }

        return await self._make_request(
            "POST",
            f"{self.BASE_URL}/comments",
            params={"part": "snippet"},
            json_data=body,
        )

    # ==================== ANALYTICS (basic) ====================

    async def get_video_stats(self, video_id: str) -> Dict[str, Any]:
        """
        Get statistics for a video.

        Args:
            video_id: YouTube video ID

        Returns:
            Video statistics (views, likes, comments, etc.)
        """
        params = {
            "part": "statistics,contentDetails",
            "id": video_id,
        }
        data = await self._make_request(
            "GET", f"{self.BASE_URL}/videos", params=params
        )
        items = data.get("items", [])
        if not items:
            raise YouTubeAPIError(f"Video {video_id} not found")
        return {
            "statistics": items[0].get("statistics", {}),
            "contentDetails": items[0].get("contentDetails", {}),
        }

    # ==================== CATEGORIES ====================

    async def get_video_categories(
        self, region_code: str = "US"
    ) -> List[Dict[str, Any]]:
        """
        Get available video categories for a region.

        Args:
            region_code: ISO 3166-1 alpha-2 country code

        Returns:
            List of video categories
        """
        params = {
            "part": "snippet",
            "regionCode": region_code,
        }
        data = await self._make_request(
            "GET", f"{self.BASE_URL}/videoCategories", params=params
        )
        return data.get("items", [])


def create_youtube_service(access_token: str) -> YouTubeService:
    """
    Create a YouTube API service instance.

    Args:
        access_token: OAuth2 access token with YouTube scopes

    Returns:
        YouTubeService instance
    """
    return YouTubeService(access_token)
