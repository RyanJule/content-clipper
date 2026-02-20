"""
Instagram Graph API Service

Handles all Instagram Graph API interactions for:
- Content publishing (photos, videos, carousels, reels, stories)
- Comment management
- Message management
- Insights and analytics
- Business account management

Meta App Review Documentation: This service demonstrates the use of all requested permissions.
"""

import httpx
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InstagramGraphAPIError(Exception):
    """Custom exception for Instagram Graph API errors"""
    pass


class InstagramGraphAPI:
    """
    Instagram Graph API client for business accounts.

    Permissions used:
    - instagram_business_basic: Get basic profile information
    - instagram_business_content_publish: Create and publish media
    - instagram_manage_comments: Read and respond to comments
    - instagram_business_manage_messages: Read and send messages
    - instagram_business_manage_insights: Access analytics data
    - pages_read_engagement: Read page engagement metrics
    - pages_show_list: List Facebook pages with Instagram accounts
    - business_management: Manage business assets
    """

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an API request to Instagram Graph API"""
        url = f"{self.BASE_URL}/{endpoint}"

        if params is None:
            params = {}
        params["access_token"] = self.access_token

        try:
            if method == "GET":
                response = await self.client.get(url, params=params)
            elif method == "POST":
                if files:
                    response = await self.client.post(url, params=params, files=files)
                else:
                    response = await self.client.post(url, params=params, data=data)
            elif method == "DELETE":
                response = await self.client.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            error_message = error_data.get("error", {}).get("message", str(e))
            logger.error(f"Instagram API error: {error_message}")
            raise InstagramGraphAPIError(error_message)
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise InstagramGraphAPIError(f"Request failed: {str(e)}")

    # ==================== PERMISSION: pages_show_list ====================

    async def get_facebook_pages(self, user_id: str = "me") -> List[Dict[str, Any]]:
        """
        Get list of Facebook Pages the user manages.

        Permission: pages_show_list
        Use case: Allow users to select which Facebook Page's Instagram account to use

        Args:
            user_id: Facebook user ID (default: "me")

        Returns:
            List of Facebook Pages with Instagram business account info
        """
        params = {
            "fields": "id,name,instagram_business_account,access_token"
        }
        response = await self._make_request("GET", f"{user_id}/accounts", params=params)
        return response.get("data", [])

    # ==================== PERMISSION: instagram_business_basic ====================

    async def get_instagram_account_info(self, ig_account_id: str) -> Dict[str, Any]:
        """
        Get Instagram Business Account information.

        Permission: instagram_business_basic
        Use case: Display account details and verify connection

        Args:
            ig_account_id: Instagram Business Account ID

        Returns:
            Account information (id, username, profile_picture_url, followers_count, etc.)
        """
        params = {
            "fields": "id,username,name,profile_picture_url,followers_count,follows_count,media_count,website,biography"
        }
        return await self._make_request("GET", ig_account_id, params=params)

    # ==================== PERMISSION: instagram_business_content_publish ====================

    async def create_image_container(
        self,
        ig_account_id: str,
        image_url: str,
        caption: Optional[str] = None,
        location_id: Optional[str] = None,
        user_tags: Optional[List[Dict[str, Any]]] = None,
        is_carousel_item: bool = False
    ) -> str:
        """
        Create a media container for a single image.

        Permission: instagram_business_content_publish
        Use case: Publish images to Instagram from scheduled posts

        Args:
            ig_account_id: Instagram Business Account ID
            image_url: Publicly accessible URL of the image
            caption: Post caption (optional)
            location_id: Location ID for geo-tagging (optional)
            user_tags: List of user tags (optional)
            is_carousel_item: Whether this image is a child item of a carousel (optional)

        Returns:
            Container ID for publishing
        """
        data = {
            "image_url": image_url,
        }

        if is_carousel_item:
            data["is_carousel_item"] = "true"
        if caption:
            data["caption"] = caption
        if location_id:
            data["location_id"] = location_id
        if user_tags:
            data["user_tags"] = user_tags

        response = await self._make_request("POST", f"{ig_account_id}/media", data=data)
        return response.get("id")

    async def create_video_container(
        self,
        ig_account_id: str,
        video_url: str,
        caption: Optional[str] = None,
        location_id: Optional[str] = None,
        thumb_offset: Optional[int] = None,
        media_type: str = "REELS"  # REELS or VIDEO
    ) -> str:
        """
        Create a media container for a video or reel.

        Permission: instagram_business_content_publish
        Use case: Publish videos and reels to Instagram from scheduled posts

        Args:
            ig_account_id: Instagram Business Account ID
            video_url: Publicly accessible URL of the video
            caption: Post caption (optional)
            location_id: Location ID for geo-tagging (optional)
            thumb_offset: Thumbnail offset in milliseconds (optional)
            media_type: "REELS" or "VIDEO"

        Returns:
            Container ID for publishing
        """
        data = {
            "media_type": media_type,
            "video_url": video_url,
        }

        if caption:
            data["caption"] = caption
        if location_id:
            data["location_id"] = location_id
        if thumb_offset:
            data["thumb_offset"] = thumb_offset

        response = await self._make_request("POST", f"{ig_account_id}/media", data=data)
        return response.get("id")

    async def create_carousel_container(
        self,
        ig_account_id: str,
        children: List[str],
        caption: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> str:
        """
        Create a carousel album container.

        Permission: instagram_business_content_publish
        Use case: Publish carousel posts with multiple images/videos

        Args:
            ig_account_id: Instagram Business Account ID
            children: List of media container IDs (created separately)
            caption: Post caption (optional)
            location_id: Location ID for geo-tagging (optional)

        Returns:
            Container ID for publishing
        """
        data = {
            "media_type": "CAROUSEL",
            "children": ",".join(children),
        }

        if caption:
            data["caption"] = caption
        if location_id:
            data["location_id"] = location_id

        response = await self._make_request("POST", f"{ig_account_id}/media", data=data)
        return response.get("id")

    async def create_story_container(
        self,
        ig_account_id: str,
        media_url: str,
        media_type: str = "IMAGE"  # IMAGE or VIDEO
    ) -> str:
        """
        Create a story container.

        Permission: instagram_business_content_publish
        Use case: Publish stories to Instagram

        Args:
            ig_account_id: Instagram Business Account ID
            media_url: Publicly accessible URL of the media
            media_type: "IMAGE" or "VIDEO"

        Returns:
            Container ID for publishing
        """
        data = {
            "media_type": "STORIES",
        }

        if media_type == "IMAGE":
            data["image_url"] = media_url
        else:
            data["video_url"] = media_url

        response = await self._make_request("POST", f"{ig_account_id}/media", data=data)
        return response.get("id")

    async def publish_container(self, ig_account_id: str, creation_id: str) -> str:
        """
        Publish a media container.

        Permission: instagram_business_content_publish
        Use case: Finalize and publish scheduled content

        Args:
            ig_account_id: Instagram Business Account ID
            creation_id: Container ID from create_*_container methods

        Returns:
            Published media ID
        """
        data = {
            "creation_id": creation_id
        }
        response = await self._make_request("POST", f"{ig_account_id}/media_publish", data=data)
        return response.get("id")

    async def check_container_status(self, container_id: str) -> Dict[str, Any]:
        """
        Check the status of a media container.

        Permission: instagram_business_content_publish
        Use case: Monitor upload progress for videos

        Args:
            container_id: Container ID

        Returns:
            Container status information
        """
        params = {
            "fields": "id,status_code,status"
        }
        return await self._make_request("GET", container_id, params=params)

    # ==================== PERMISSION: instagram_manage_comments ====================

    async def get_media_comments(
        self,
        media_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get comments on a media object.

        Permission: instagram_manage_comments
        Use case: Display and moderate comments on published posts

        Args:
            media_id: Instagram media ID
            limit: Maximum number of comments to retrieve

        Returns:
            List of comments with text, username, timestamp, etc.
        """
        params = {
            "fields": "id,text,username,timestamp,like_count,replies",
            "limit": limit
        }
        response = await self._make_request("GET", f"{media_id}/comments", params=params)
        return response.get("data", [])

    async def reply_to_comment(
        self,
        comment_id: str,
        message: str
    ) -> str:
        """
        Reply to a comment.

        Permission: instagram_manage_comments
        Use case: Respond to user comments for engagement

        Args:
            comment_id: Comment ID to reply to
            message: Reply message text

        Returns:
            New comment ID
        """
        data = {
            "message": message
        }
        response = await self._make_request("POST", f"{comment_id}/replies", data=data)
        return response.get("id")

    async def delete_comment(self, comment_id: str) -> bool:
        """
        Delete a comment.

        Permission: instagram_manage_comments
        Use case: Moderate inappropriate comments

        Args:
            comment_id: Comment ID to delete

        Returns:
            True if successful
        """
        response = await self._make_request("DELETE", comment_id)
        return response.get("success", False)

    async def hide_comment(self, comment_id: str, hide: bool = True) -> bool:
        """
        Hide or unhide a comment.

        Permission: instagram_manage_comments
        Use case: Moderate comments without deleting them

        Args:
            comment_id: Comment ID
            hide: True to hide, False to unhide

        Returns:
            True if successful
        """
        data = {
            "hide": hide
        }
        response = await self._make_request("POST", comment_id, data=data)
        return response.get("success", False)

    # ==================== PERMISSION: instagram_business_manage_messages ====================

    async def get_conversations(
        self,
        ig_account_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get Instagram Direct message conversations.

        Permission: instagram_business_manage_messages
        Use case: Display user messages for customer support

        Args:
            ig_account_id: Instagram Business Account ID
            limit: Maximum number of conversations to retrieve

        Returns:
            List of conversations
        """
        params = {
            "fields": "id,participants,updated_time,messages{message,from,created_time}",
            "limit": limit
        }
        response = await self._make_request("GET", f"{ig_account_id}/conversations", params=params)
        return response.get("data", [])

    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get messages in a conversation.

        Permission: instagram_business_manage_messages
        Use case: View message history for customer support

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to retrieve

        Returns:
            List of messages
        """
        params = {
            "fields": "id,message,from,created_time,attachments",
            "limit": limit
        }
        response = await self._make_request("GET", f"{conversation_id}/messages", params=params)
        return response.get("data", [])

    async def send_message(
        self,
        ig_account_id: str,
        recipient_id: str,
        message: str
    ) -> str:
        """
        Send a direct message.

        Permission: instagram_business_manage_messages
        Use case: Reply to customer inquiries

        Args:
            ig_account_id: Instagram Business Account ID
            recipient_id: Instagram user ID of recipient
            message: Message text

        Returns:
            Message ID
        """
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message}
        }
        response = await self._make_request("POST", f"{ig_account_id}/messages", data=data)
        return response.get("id")

    # ==================== PERMISSION: instagram_business_manage_insights ====================

    async def get_account_insights(
        self,
        ig_account_id: str,
        metrics: List[str],
        period: str = "day",
        since: Optional[int] = None,
        until: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get account-level insights.

        Permission: instagram_business_manage_insights
        Use case: Display analytics dashboard for account performance

        Args:
            ig_account_id: Instagram Business Account ID
            metrics: List of metrics (e.g., ["impressions", "reach", "profile_views"])
            period: Time period - "day", "week", "days_28", "lifetime"
            since: Unix timestamp for start date
            until: Unix timestamp for end date

        Returns:
            List of insights data
        """
        params = {
            "metric": ",".join(metrics),
            "period": period
        }

        if since:
            params["since"] = since
        if until:
            params["until"] = until

        response = await self._make_request("GET", f"{ig_account_id}/insights", params=params)
        return response.get("data", [])

    async def get_media_insights(
        self,
        media_id: str,
        metrics: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get insights for a specific media object.

        Permission: instagram_business_manage_insights
        Use case: Display performance metrics for individual posts

        Args:
            media_id: Instagram media ID
            metrics: List of metrics (e.g., ["engagement", "impressions", "reach", "saved"])

        Returns:
            List of insights data
        """
        params = {
            "metric": ",".join(metrics)
        }
        response = await self._make_request("GET", f"{media_id}/insights", params=params)
        return response.get("data", [])

    async def get_story_insights(
        self,
        media_id: str,
        metrics: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get insights for a story.

        Permission: instagram_business_manage_insights
        Use case: Track story performance metrics

        Args:
            media_id: Instagram story media ID
            metrics: List of metrics (e.g., ["impressions", "reach", "replies", "exits"])

        Returns:
            List of insights data
        """
        params = {
            "metric": ",".join(metrics)
        }
        response = await self._make_request("GET", f"{media_id}/insights", params=params)
        return response.get("data", [])

    # ==================== PERMISSION: pages_read_engagement ====================

    async def get_page_insights(
        self,
        page_id: str,
        metrics: List[str],
        period: str = "day",
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get Facebook Page engagement insights.

        Permission: pages_read_engagement
        Use case: Display Facebook Page analytics for linked Instagram accounts

        Args:
            page_id: Facebook Page ID
            metrics: List of metrics (e.g., ["page_impressions", "page_engaged_users"])
            period: Time period - "day", "week", "days_28"
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)

        Returns:
            List of insights data
        """
        params = {
            "metric": ",".join(metrics),
            "period": period
        }

        if since:
            params["since"] = since
        if until:
            params["until"] = until

        response = await self._make_request("GET", f"{page_id}/insights", params=params)
        return response.get("data", [])

    # ==================== MEDIA MANAGEMENT ====================

    async def get_user_media(
        self,
        ig_account_id: str,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Get user's published media.

        Permission: instagram_business_basic
        Use case: Display user's posted content

        Args:
            ig_account_id: Instagram Business Account ID
            limit: Maximum number of media items to retrieve

        Returns:
            List of media objects
        """
        params = {
            "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count",
            "limit": limit
        }
        response = await self._make_request("GET", f"{ig_account_id}/media", params=params)
        return response.get("data", [])

    async def get_media_details(self, media_id: str) -> Dict[str, Any]:
        """
        Get details about a specific media object.

        Permission: instagram_business_basic
        Use case: Display detailed information about a post

        Args:
            media_id: Instagram media ID

        Returns:
            Media object details
        """
        params = {
            "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,username,like_count,comments_count,is_comment_enabled"
        }
        return await self._make_request("GET", media_id, params=params)


# Helper function to create service instance
def create_instagram_service(access_token: str) -> InstagramGraphAPI:
    """
    Create an Instagram Graph API service instance.

    Args:
        access_token: User or Page access token with required permissions

    Returns:
        InstagramGraphAPI instance
    """
    return InstagramGraphAPI(access_token)
