"""
LinkedIn Community Management API Service

Handles all LinkedIn API interactions for:
- Text post publishing
- Image post publishing (with image upload)
- Video post publishing (with video upload)
- Article sharing
- Company/organization page posting
- Profile and organization info
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class LinkedInAPIError(Exception):
    """Custom exception for LinkedIn API errors"""
    pass


class LinkedInService:
    """
    LinkedIn Community Management API client.

    Uses the versioned REST API (v2) with LinkedIn-Version header.

    Scopes required:
    - openid, profile, email: Authentication and profile access
    - w_member_social: Post on behalf of authenticated member
    - r_organization_social: Read organization posts
    - w_organization_social: Post on behalf of organizations
    """

    BASE_URL = "https://api.linkedin.com"
    REST_URL = "https://api.linkedin.com/rest"
    API_VERSION = "202401"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "LinkedIn-Version": self.API_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
        }
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, read=120.0),
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
        """Make an API request to LinkedIn API"""
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
                else:
                    response = await self.client.put(
                        url, params=params, json=json_data, headers=headers
                    )
            elif method == "DELETE":
                response = await self.client.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            if response.status_code == 204:
                return {"success": True}

            # Some LinkedIn endpoints return empty body with 201
            if response.status_code == 201:
                # Check for x-restli-id header (post URN)
                restli_id = response.headers.get("x-restli-id", "")
                try:
                    body = response.json()
                except Exception:
                    body = {}
                body["restli_id"] = restli_id
                return body

            return response.json()

        except httpx.HTTPStatusError as e:
            error_data = {}
            try:
                error_data = e.response.json()
            except Exception:
                pass
            error_msg = (
                error_data.get("message", "")
                or error_data.get("error", "")
                or str(e)
            )
            logger.error(f"LinkedIn API error ({e.response.status_code}): {error_msg}")
            raise LinkedInAPIError(f"LinkedIn API error: {error_msg}")
        except httpx.TimeoutException:
            raise LinkedInAPIError("LinkedIn API request timed out")
        except Exception as e:
            logger.error(f"LinkedIn request failed: {str(e)}")
            raise LinkedInAPIError(f"Request failed: {str(e)}")

    # ==================== PROFILE INFO ====================

    async def get_profile(self) -> Dict[str, Any]:
        """
        Get the authenticated user's LinkedIn profile info.

        Returns:
            Profile data including sub (person ID), name, email, picture
        """
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/v2/userinfo",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "id": data.get("sub", ""),
                "name": data.get("name", ""),
                "email": data.get("email", ""),
                "picture": data.get("picture", ""),
                "person_urn": f"urn:li:person:{data.get('sub', '')}",
            }

    # ==================== ORGANIZATIONS ====================

    async def get_organizations(self) -> List[Dict[str, Any]]:
        """
        Get organizations (company pages) the user is an admin of.

        Returns:
            List of organization data with id, name, and URN
        """
        url = f"{self.REST_URL}/organizationAcls"
        params = {
            "q": "roleAssignee",
            "role": "ADMINISTRATOR",
            "projection": "(elements*(organization~(id,localizedName,logoV2)))",
        }

        try:
            data = await self._make_request("GET", url, params=params)
            organizations = []
            for element in data.get("elements", []):
                org = element.get("organization~", element.get("organization", {}))
                if isinstance(org, str):
                    # org is a URN string, need to resolve it
                    org_id = org.split(":")[-1]
                    organizations.append({
                        "id": org_id,
                        "name": f"Organization {org_id}",
                        "urn": org if org.startswith("urn:") else f"urn:li:organization:{org_id}",
                    })
                else:
                    org_id = org.get("id", element.get("organization", "").split(":")[-1])
                    organizations.append({
                        "id": str(org_id),
                        "name": org.get("localizedName", f"Organization {org_id}"),
                        "urn": f"urn:li:organization:{org_id}",
                    })
            return organizations
        except LinkedInAPIError as e:
            logger.warning(f"Could not fetch organizations: {e}")
            return []

    # ==================== TEXT POSTS ====================

    async def create_text_post(
        self,
        author_urn: str,
        text: str,
        visibility: str = "PUBLIC",
    ) -> Dict[str, Any]:
        """
        Create a text-only post on LinkedIn.

        Args:
            author_urn: Author URN (urn:li:person:{id} or urn:li:organization:{id})
            text: Post text content (max 3000 characters)
            visibility: "PUBLIC", "CONNECTIONS", or "LOGGED_IN"

        Returns:
            Post creation result with post URN
        """
        body = {
            "author": author_urn,
            "commentary": text[:3000],
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
        }

        result = await self._make_request(
            "POST",
            f"{self.REST_URL}/posts",
            json_data=body,
        )

        post_urn = result.get("restli_id", "")
        logger.info(f"Created LinkedIn text post: {post_urn}")

        return {
            "post_urn": post_urn,
            "post_url": self._build_post_url(post_urn, author_urn),
        }

    # ==================== IMAGE POSTS ====================

    async def initialize_image_upload(
        self,
        owner_urn: str,
    ) -> Dict[str, str]:
        """
        Initialize an image upload to LinkedIn.

        Args:
            owner_urn: Owner URN (person or organization)

        Returns:
            Dict with upload_url and image asset URN
        """
        body = {
            "initializeUploadRequest": {
                "owner": owner_urn,
            }
        }

        result = await self._make_request(
            "POST",
            f"{self.REST_URL}/images?action=initializeUpload",
            json_data=body,
        )

        upload_data = result.get("value", result)
        return {
            "upload_url": upload_data.get("uploadUrl", ""),
            "image_urn": upload_data.get("image", ""),
        }

    async def upload_image_binary(
        self,
        upload_url: str,
        image_data: bytes,
        content_type: str = "image/jpeg",
    ) -> None:
        """
        Upload image binary data to LinkedIn's upload URL.

        Args:
            upload_url: The upload URL from initializeUpload
            image_data: Raw image bytes
            content_type: MIME type of the image
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": content_type,
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=120.0)) as client:
            response = await client.put(
                upload_url,
                content=image_data,
                headers=headers,
            )
            response.raise_for_status()

        logger.info("Image binary uploaded successfully")

    async def create_image_post(
        self,
        author_urn: str,
        text: str,
        image_data: bytes,
        content_type: str = "image/jpeg",
        alt_text: str = "",
        visibility: str = "PUBLIC",
    ) -> Dict[str, Any]:
        """
        Upload an image and create a post with it.

        Args:
            author_urn: Author URN (person or organization)
            text: Post text content
            image_data: Raw image bytes
            content_type: MIME type of the image
            alt_text: Alternative text for the image
            visibility: Post visibility

        Returns:
            Post creation result with post URN
        """
        # Step 1: Initialize upload
        upload_info = await self.initialize_image_upload(author_urn)
        image_urn = upload_info["image_urn"]

        # Step 2: Upload image binary
        await self.upload_image_binary(
            upload_info["upload_url"],
            image_data,
            content_type,
        )

        # Step 3: Create post with image
        body = {
            "author": author_urn,
            "commentary": text[:3000],
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "media": {
                    "id": image_urn,
                    "altText": alt_text or "Image",
                }
            },
            "lifecycleState": "PUBLISHED",
        }

        result = await self._make_request(
            "POST",
            f"{self.REST_URL}/posts",
            json_data=body,
        )

        post_urn = result.get("restli_id", "")
        logger.info(f"Created LinkedIn image post: {post_urn}")

        return {
            "post_urn": post_urn,
            "image_urn": image_urn,
            "post_url": self._build_post_url(post_urn, author_urn),
        }

    # ==================== VIDEO POSTS ====================

    async def initialize_video_upload(
        self,
        owner_urn: str,
        file_size: int,
    ) -> Dict[str, Any]:
        """
        Initialize a video upload to LinkedIn.

        Args:
            owner_urn: Owner URN (person or organization)
            file_size: Size of the video file in bytes

        Returns:
            Dict with upload_url, video URN, and upload instructions
        """
        body = {
            "initializeUploadRequest": {
                "owner": owner_urn,
                "fileSizeBytes": file_size,
            }
        }

        result = await self._make_request(
            "POST",
            f"{self.REST_URL}/videos?action=initializeUpload",
            json_data=body,
        )

        upload_data = result.get("value", result)
        upload_instructions = upload_data.get("uploadInstructions", [])

        return {
            "video_urn": upload_data.get("video", ""),
            "upload_instructions": upload_instructions,
            "upload_token": upload_data.get("uploadToken", ""),
        }

    async def upload_video_part(
        self,
        upload_url: str,
        video_data: bytes,
    ) -> str:
        """
        Upload a single part of video data.

        Args:
            upload_url: The upload URL for this part
            video_data: Raw video bytes for this part

        Returns:
            ETag from the upload response
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream",
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=300.0)) as client:
            response = await client.put(
                upload_url,
                content=video_data,
                headers=headers,
            )
            response.raise_for_status()

        etag = response.headers.get("etag", "")
        return etag

    async def finalize_video_upload(
        self,
        video_urn: str,
        upload_token: str,
        etags: List[str],
    ) -> None:
        """
        Finalize the video upload after all parts are uploaded.

        Args:
            video_urn: Video URN from initialize
            upload_token: Upload token from initialize
            etags: List of ETags from each uploaded part
        """
        body = {
            "finalizeUploadRequest": {
                "video": video_urn,
                "uploadToken": upload_token,
                "uploadedPartIds": etags,
            }
        }

        await self._make_request(
            "POST",
            f"{self.REST_URL}/videos?action=finalizeUpload",
            json_data=body,
        )

        logger.info(f"Finalized video upload: {video_urn}")

    async def wait_for_video_processing(
        self,
        video_urn: str,
        max_attempts: int = 60,
        poll_interval: int = 5,
    ) -> bool:
        """
        Wait for a video to finish processing on LinkedIn.

        Args:
            video_urn: Video URN to check
            max_attempts: Maximum polling attempts
            poll_interval: Seconds between polls

        Returns:
            True if video is ready
        """
        encoded_urn = video_urn.replace(":", "%3A")
        url = f"{self.REST_URL}/videos/{encoded_urn}"

        for attempt in range(max_attempts):
            try:
                result = await self._make_request("GET", url)
                status = result.get("status", "")
                if status == "AVAILABLE":
                    return True
                if status in ("PROCESSING_FAILED", "WAITING_UPLOAD"):
                    if attempt > 5 and status == "WAITING_UPLOAD":
                        raise LinkedInAPIError("Video upload was not received by LinkedIn")
                    if status == "PROCESSING_FAILED":
                        raise LinkedInAPIError("Video processing failed on LinkedIn")
            except LinkedInAPIError:
                raise
            except Exception:
                pass

            await asyncio.sleep(poll_interval)

        raise LinkedInAPIError("Video processing timed out")

    async def create_video_post(
        self,
        author_urn: str,
        text: str,
        video_data: bytes,
        title: str = "",
        visibility: str = "PUBLIC",
    ) -> Dict[str, Any]:
        """
        Upload a video and create a post with it.

        Args:
            author_urn: Author URN (person or organization)
            text: Post text content
            video_data: Raw video bytes
            title: Video title
            visibility: Post visibility

        Returns:
            Post creation result with post URN
        """
        # Step 1: Initialize upload
        upload_info = await self.initialize_video_upload(
            owner_urn=author_urn,
            file_size=len(video_data),
        )
        video_urn = upload_info["video_urn"]
        upload_token = upload_info["upload_token"]
        instructions = upload_info["upload_instructions"]

        # Step 2: Upload video parts
        etags = []
        for instruction in instructions:
            upload_url = instruction.get("uploadUrl", "")
            first_byte = instruction.get("firstByte", 0)
            last_byte = instruction.get("lastByte", len(video_data) - 1)

            chunk = video_data[first_byte:last_byte + 1]
            etag = await self.upload_video_part(upload_url, chunk)
            etags.append(etag)

        # Step 3: Finalize upload
        await self.finalize_video_upload(video_urn, upload_token, etags)

        # Step 4: Wait for processing
        await self.wait_for_video_processing(video_urn)

        # Step 5: Create post with video
        body = {
            "author": author_urn,
            "commentary": text[:3000],
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "media": {
                    "id": video_urn,
                    "title": title or "Video",
                }
            },
            "lifecycleState": "PUBLISHED",
        }

        result = await self._make_request(
            "POST",
            f"{self.REST_URL}/posts",
            json_data=body,
        )

        post_urn = result.get("restli_id", "")
        logger.info(f"Created LinkedIn video post: {post_urn}")

        return {
            "post_urn": post_urn,
            "video_urn": video_urn,
            "post_url": self._build_post_url(post_urn, author_urn),
        }

    # ==================== ARTICLE POSTS ====================

    async def create_article_post(
        self,
        author_urn: str,
        text: str,
        article_url: str,
        title: str = "",
        description: str = "",
        visibility: str = "PUBLIC",
    ) -> Dict[str, Any]:
        """
        Create a post sharing an article/URL.

        Args:
            author_urn: Author URN (person or organization)
            text: Post commentary text
            article_url: URL of the article to share
            title: Article title (optional, LinkedIn auto-fetches)
            description: Article description (optional)
            visibility: Post visibility

        Returns:
            Post creation result with post URN
        """
        body = {
            "author": author_urn,
            "commentary": text[:3000],
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "article": {
                    "source": article_url,
                    "title": title or article_url,
                    "description": description,
                }
            },
            "lifecycleState": "PUBLISHED",
        }

        result = await self._make_request(
            "POST",
            f"{self.REST_URL}/posts",
            json_data=body,
        )

        post_urn = result.get("restli_id", "")
        logger.info(f"Created LinkedIn article post: {post_urn}")

        return {
            "post_urn": post_urn,
            "post_url": self._build_post_url(post_urn, author_urn),
        }

    # ==================== POST MANAGEMENT ====================

    async def get_posts(
        self,
        author_urn: str,
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get posts by the specified author.

        Args:
            author_urn: Author URN (person or organization)
            count: Number of posts to return

        Returns:
            List of post data
        """
        params = {
            "author": author_urn,
            "q": "author",
            "count": min(count, 100),
        }

        result = await self._make_request(
            "GET",
            f"{self.REST_URL}/posts",
            params=params,
        )

        return result.get("elements", [])

    async def delete_post(self, post_urn: str) -> bool:
        """
        Delete a LinkedIn post.

        Args:
            post_urn: Post URN to delete

        Returns:
            True if successful
        """
        encoded_urn = post_urn.replace(":", "%3A")
        await self._make_request(
            "DELETE",
            f"{self.REST_URL}/posts/{encoded_urn}",
        )
        logger.info(f"Deleted LinkedIn post: {post_urn}")
        return True

    # ==================== HELPERS ====================

    @staticmethod
    def _build_post_url(post_urn: str, author_urn: str) -> str:
        """Build a LinkedIn post URL from the post URN."""
        # Extract the activity ID from URN like urn:li:share:123 or urn:li:ugcPost:123
        if not post_urn:
            return ""
        parts = post_urn.split(":")
        if len(parts) >= 4:
            activity_id = parts[-1]
            if "organization" in author_urn:
                org_id = author_urn.split(":")[-1]
                return f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}/"
            return f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}/"
        return f"https://www.linkedin.com/feed/"


def create_linkedin_service(access_token: str) -> LinkedInService:
    """
    Create a LinkedIn API service instance.

    Args:
        access_token: OAuth2 access token with LinkedIn scopes

    Returns:
        LinkedInService instance
    """
    return LinkedInService(access_token)
