# backend/app/services/oauth_service.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.crypto import decrypt_token, encrypt_token
from app.models.account import Account

logger = logging.getLogger(__name__)


class OAuthProvider:
    """Base class for OAuth providers"""

    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None
        self.authorization_url = None
        self.token_url = None
        self.scope = []
        self.platform_name = None

    def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scope),
            "state": state,
        }
        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh an expired access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> Dict:
        """Get user profile information"""
        raise NotImplementedError("Subclasses must implement get_user_info")


class InstagramOAuth(OAuthProvider):
    """
    Instagram OAuth (via Facebook Graph API)

    This uses Facebook Login to get access to Instagram Business/Creator accounts.
    Required for Instagram Graph API access.
    """

    def __init__(self):
        super().__init__()
        import logging
        logger = logging.getLogger(__name__)

        self.platform_name = "instagram"
        self.client_id = settings.INSTAGRAM_CLIENT_ID
        self.client_secret = settings.INSTAGRAM_CLIENT_SECRET

        # Validate credentials are configured
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Instagram/Facebook OAuth credentials not configured. "
                "Please set INSTAGRAM_CLIENT_ID and INSTAGRAM_CLIENT_SECRET in your .env file. "
                "Get these from https://developers.facebook.com/apps"
            )

        self.redirect_uri = f"{settings.BACKEND_URL}/api/v1/oauth/instagram/callback"
        # Use Facebook OAuth for Instagram Business API access
        self.authorization_url = "https://www.facebook.com/v18.0/dialog/oauth"
        self.token_url = "https://graph.facebook.com/v18.0/oauth/access_token"

        # Check if we should use minimal permissions for testing
        # Set INSTAGRAM_USE_MINIMAL_PERMISSIONS=true in .env for testing without Instagram Graph API product
        use_minimal = settings.ENVIRONMENT == "development" and not hasattr(settings, 'INSTAGRAM_USE_FULL_PERMISSIONS')

        if use_minimal:
            # Minimal permissions that work without Instagram Graph API product
            # Use these for initial OAuth testing
            logger.warning("Using minimal Instagram permissions for testing. Add Instagram Graph API product to your Facebook app for full functionality.")
            self.scope = [
                "public_profile",                           # Public profile info
                "pages_show_list",                          # List pages
                "business_management",                      # Manage business assets
            ]
        else:
            # All permissions required for full Instagram functionality
            self.scope = [
                "public_profile",                           # Public profile info
                "pages_show_list",                          # List pages
                "pages_read_engagement",                    # Read page engagement
                "business_management",                      # Manage business assets
                "instagram_basic",                          # Basic Instagram access
                "instagram_business_basic",                 # Instagram Business basic info
                "instagram_business_content_publish",       # Publish content
                "instagram_manage_comments",                # Manage comments
                "instagram_business_manage_messages",       # Manage DMs
                "instagram_business_manage_insights",       # Access insights
                "instagram_manage_messages",                # Manage messages (legacy)
            ]

    def get_authorization_url(self, state: str) -> str:
        """
        Override to add config_id for Instagram

        Note: For production, you may want to add a config_id parameter
        to pre-select the Instagram account in the OAuth flow
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": ",".join(self.scope),  # Facebook uses comma-separated scopes
            "state": state,
            "auth_type": "rerequest",  # Ask for permissions even if previously denied
        }
        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_for_long_lived_token(self, short_lived_token: str) -> Dict:
        """
        Exchange a short-lived user token for a long-lived token (~60 days).

        Facebook/Instagram uses the fb_exchange_token grant type instead of
        traditional refresh tokens. This should be called right after the
        initial OAuth code exchange.
        """
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "fb_exchange_token": short_lived_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.token_url, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info(
                "Exchanged short-lived token for long-lived token "
                f"(expires_in={data.get('expires_in')}s)"
            )
            return data

    async def refresh_access_token(self, access_token: str) -> Dict:
        """
        Refresh a long-lived Facebook/Instagram token.

        Instagram does not use refresh_token grants. Instead, valid long-lived
        tokens are refreshed by exchanging them again via fb_exchange_token.
        The token must not be expired — refresh before the ~60 day expiry.

        Args:
            access_token: The current long-lived token (NOT a refresh token).

        Returns:
            Dict with access_token, token_type, and expires_in.
        """
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "fb_exchange_token": access_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.token_url, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info(
                "Refreshed long-lived Instagram token "
                f"(expires_in={data.get('expires_in')}s)"
            )
            return data

    async def refresh_page_access_token(self, user_access_token: str, page_id: str) -> Optional[str]:
        """
        Retrieve a fresh page access token using the refreshed user token.

        Page tokens derived from long-lived user tokens are themselves
        long-lived (non-expiring for pages you manage).

        Args:
            user_access_token: A valid long-lived user access token.
            page_id: The Facebook Page ID.

        Returns:
            The page access token, or None if the page wasn't found.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.facebook.com/v18.0/me/accounts",
                params={
                    "fields": "id,access_token",
                    "access_token": user_access_token,
                },
            )
            response.raise_for_status()
            pages = response.json().get("data", [])

            for page in pages:
                if page["id"] == page_id:
                    return page.get("access_token")

        logger.warning(f"Page {page_id} not found when refreshing page token")
        return None

    async def get_user_info(self, access_token: str) -> Dict:
        """
        Get Facebook user profile and Instagram Business Account

        This method:
        1. Gets the Facebook user's pages
        2. Finds pages with Instagram Business Accounts
        3. Returns the first Instagram Business Account found
        """
        async with httpx.AsyncClient() as client:
            # Get Facebook user ID
            me_response = await client.get(
                f"https://graph.facebook.com/v18.0/me?access_token={access_token}"
            )
            me_response.raise_for_status()
            fb_user = me_response.json()

            # Get pages managed by this user
            pages_response = await client.get(
                f"https://graph.facebook.com/v18.0/me/accounts",
                params={
                    "fields": "id,name,instagram_business_account,access_token",
                    "access_token": access_token
                }
            )
            pages_response.raise_for_status()
            pages_data = pages_response.json()

            # Find first page with Instagram Business Account
            instagram_account = None
            page_access_token = None
            page_id = None

            for page in pages_data.get("data", []):
                if "instagram_business_account" in page:
                    page_id = page["id"]
                    page_access_token = page.get("access_token", access_token)
                    ig_account_id = page["instagram_business_account"]["id"]

                    # Get Instagram account details
                    ig_response = await client.get(
                        f"https://graph.facebook.com/v18.0/{ig_account_id}",
                        params={
                            "fields": "id,username,name,profile_picture_url",
                            "access_token": page_access_token
                        }
                    )
                    ig_response.raise_for_status()
                    instagram_account = ig_response.json()
                    instagram_account["page_id"] = page_id
                    instagram_account["page_name"] = page["name"]
                    instagram_account["page_access_token"] = page_access_token
                    break

            if not instagram_account:
                raise ValueError(
                    "No Instagram Business Account found. Please connect an Instagram "
                    "Business or Creator account to your Facebook Page first."
                )

            return {
                "id": instagram_account["id"],
                "username": instagram_account.get("username", ""),
                "name": instagram_account.get("name", ""),
                "profile_picture_url": instagram_account.get("profile_picture_url", ""),
                "facebook_user_id": fb_user["id"],
                "facebook_page_id": instagram_account["page_id"],
                "facebook_page_name": instagram_account["page_name"],
                "instagram_business_account_id": instagram_account["id"],
                # Use page access token for API calls (more permissions)
                "access_token": instagram_account["page_access_token"],
            }


class YouTubeOAuth(OAuthProvider):
    """
    YouTube OAuth (via Google OAuth 2.0)

    Provides access to YouTube Data API v3 for:
    - Video uploads (standard and resumable)
    - Shorts publishing
    - Community posts
    - Thumbnail management
    - Channel management
    """

    def __init__(self):
        super().__init__()
        self.platform_name = "youtube"
        self.client_id = settings.YOUTUBE_CLIENT_ID
        self.client_secret = settings.YOUTUBE_CLIENT_SECRET

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "YouTube/Google OAuth credentials not configured. "
                "Please set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in your .env file. "
                "Get these from https://console.cloud.google.com/apis/credentials"
            )

        self.redirect_uri = f"{settings.BACKEND_URL}/api/v1/oauth/youtube/callback"
        self.authorization_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.scope = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube.force-ssl",
        ]

    def get_authorization_url(self, state: str) -> str:
        """Override to add access_type and prompt for offline refresh tokens"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scope),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
        }
        return f"{self.authorization_url}?{urlencode(params)}"

    async def get_user_info(self, access_token: str) -> Dict:
        """Get YouTube channel info including snippet and statistics"""
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            "part": "snippet,statistics,contentDetails",
            "mine": "true",
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get("items"):
                channel = data["items"][0]
                snippet = channel.get("snippet", {})
                statistics = channel.get("statistics", {})
                return {
                    "id": channel["id"],
                    "username": snippet.get("title", ""),
                    "channel_id": channel["id"],
                    "channel_title": snippet.get("title", ""),
                    "channel_description": snippet.get("description", ""),
                    "channel_thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                    "subscriber_count": statistics.get("subscriberCount", "0"),
                    "video_count": statistics.get("videoCount", "0"),
                    "view_count": statistics.get("viewCount", "0"),
                    "uploads_playlist_id": channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads", ""),
                }
            raise ValueError(
                "No YouTube channel found for this Google account. "
                "Please create a YouTube channel first."
            )


class LinkedInOAuth(OAuthProvider):
    """LinkedIn OAuth"""

    def __init__(self):
        super().__init__()
        self.platform_name = "linkedin"
        self.client_id = settings.LINKEDIN_CLIENT_ID
        self.client_secret = settings.LINKEDIN_CLIENT_SECRET
        self.redirect_uri = f"{settings.BACKEND_URL}/api/v1/oauth/linkedin/callback"
        self.authorization_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.scope = ["r_liteprofile", "r_emailaddress", "w_member_social"]

    async def get_user_info(self, access_token: str) -> Dict:
        """Get LinkedIn user profile"""
        url = "https://api.linkedin.com/v2/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {
                "id": data["id"],
                "username": f"{data.get('localizedFirstName', '')} {data.get('localizedLastName', '')}".strip(),
            }


class TikTokOAuth(OAuthProvider):
    """TikTok OAuth"""

    def __init__(self):
        super().__init__()
        self.platform_name = "tiktok"
        self.client_id = settings.TIKTOK_CLIENT_KEY
        self.client_secret = settings.TIKTOK_CLIENT_SECRET
        self.redirect_uri = f"{settings.BACKEND_URL}/api/v1/oauth/tiktok/callback"
        self.authorization_url = "https://www.tiktok.com/v2/auth/authorize"
        self.token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        self.scope = ["user.info.basic", "video.upload", "video.publish"]

    def get_authorization_url(self, state: str) -> str:
        """TikTok uses different parameter names"""
        params = {
            "client_key": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": ",".join(self.scope),
            "state": state,
        }
        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict:
        """TikTok token exchange.

        TikTok API v2 wraps token data inside a ``{"data": {...}}`` envelope.
        This method unwraps it so callers receive a flat dict with
        ``access_token``, ``refresh_token``, ``expires_in``, etc.
        """
        data = {
            "client_key": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                json=data,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()

            # TikTok nests token data under a "data" key
            token_data = result.get("data", result)

            if not token_data.get("access_token"):
                error = result.get("error", "Unknown error")
                if isinstance(error, dict):
                    error_msg = error.get("message", "Unknown error")
                else:
                    error_msg = str(error)
                description = result.get("error_description", "")
                if description:
                    error_msg = f"{error_msg}: {description}"
                raise ValueError(f"TikTok token exchange failed: {error_msg}")

            return token_data

    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh a TikTok access token.

        TikTok uses ``client_key`` instead of ``client_id`` and requires a
        JSON request body, so the base-class implementation does not work.
        """
        data = {
            "client_key": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                json=data,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()
            token_data = result.get("data", result)

            if not token_data.get("access_token"):
                error_msg = result.get("error", {}).get("message", "Unknown error")
                raise ValueError(f"TikTok token refresh failed: {error_msg}")

            return token_data

    async def get_user_info(self, access_token: str) -> Dict:
        """Get TikTok user info via the v2 user info endpoint."""
        url = "https://open.tiktokapis.com/v2/user/info/?fields=open_id,display_name,avatar_url"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            user_data = data.get("data", {}).get("user", {})
            return {
                "id": user_data.get("open_id"),
                "username": user_data.get("display_name"),
                "avatar_url": user_data.get("avatar_url", ""),
            }


# Provider registry
OAUTH_PROVIDERS = {
    "instagram": InstagramOAuth,
    "youtube": YouTubeOAuth,
    "linkedin": LinkedInOAuth,
    "tiktok": TikTokOAuth,
}


def get_oauth_provider(platform: str) -> OAuthProvider:
    """Get OAuth provider instance"""
    provider_class = OAUTH_PROVIDERS.get(platform)
    if not provider_class:
        raise ValueError(f"Unsupported platform: {platform}")
    return provider_class()


async def save_oauth_tokens(
    db: Session,
    user_id: int,
    platform: str,
    token_data: Dict,
    user_info: Dict,
) -> Account:
    """Save OAuth tokens to database"""
    # Calculate token expiration
    expires_in = token_data.get("expires_in")
    token_expires_at = None
    if expires_in:
        token_expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))

    # Check if account already exists
    existing_account = (
        db.query(Account)
        .filter(Account.user_id == user_id, Account.platform == platform)
        .first()
    )

    if existing_account:
        # Update existing account
        existing_account.access_token_enc = encrypt_token(
            token_data.get("access_token")
        )
        existing_account.refresh_token_enc = encrypt_token(
            token_data.get("refresh_token")
        )
        existing_account.token_expires_at = token_expires_at
        existing_account.is_active = True
        existing_account.account_username = user_info.get("username", "")
        existing_account.meta_info = user_info
        db.commit()
        db.refresh(existing_account)
        return existing_account
    else:
        # Create new account
        new_account = Account(
            user_id=user_id,
            platform=platform,
            account_username=user_info.get("username", ""),
            access_token_enc=encrypt_token(token_data.get("access_token")),
            refresh_token_enc=encrypt_token(token_data.get("refresh_token")),
            token_expires_at=token_expires_at,
            is_active=True,
            meta_info=user_info,
        )
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
        return new_account


async def refresh_account_token(db: Session, account: Account) -> Account:
    """Refresh an expired access token.

    For Instagram/Facebook, the long-lived access token is refreshed via
    fb_exchange_token (no refresh_token involved). For other providers,
    the standard refresh_token grant is used.
    """
    provider = get_oauth_provider(account.platform)

    if account.platform == "instagram":
        # Instagram: refresh the long-lived user token, then update the page token
        access_token = decrypt_token(account.access_token_enc)
        if not access_token:
            raise ValueError("No access token available for Instagram refresh")

        try:
            token_data = await provider.refresh_access_token(access_token)

            new_access_token = token_data.get("access_token")
            account.access_token_enc = encrypt_token(new_access_token)

            expires_in = token_data.get("expires_in")
            if expires_in:
                account.token_expires_at = datetime.utcnow() + timedelta(
                    seconds=int(expires_in)
                )

            # Refresh the page access token stored in meta_info
            meta_info = account.meta_info or {}
            page_id = meta_info.get("facebook_page_id")
            if page_id:
                page_token = await provider.refresh_page_access_token(
                    new_access_token, page_id
                )
                if page_token:
                    meta_info["access_token"] = page_token
                    account.meta_info = meta_info
                else:
                    logger.warning(
                        f"Could not refresh page token for account {account.id}"
                    )

            db.commit()
            db.refresh(account)

            logger.info(
                f"Refreshed Instagram token for account {account.id}"
            )
            return account

        except Exception as e:
            logger.error(
                f"Failed to refresh Instagram token for account {account.id}: {e}"
            )
            account.is_active = False
            db.commit()
            raise
    else:
        # Standard OAuth refresh_token flow (YouTube, LinkedIn, TikTok)
        refresh_token = decrypt_token(account.refresh_token_enc)
        if not refresh_token:
            raise ValueError("No refresh token available")

        try:
            token_data = await provider.refresh_access_token(refresh_token)

            account.access_token_enc = encrypt_token(token_data.get("access_token"))

            if token_data.get("refresh_token"):
                account.refresh_token_enc = encrypt_token(token_data["refresh_token"])

            expires_in = token_data.get("expires_in")
            if expires_in:
                account.token_expires_at = datetime.utcnow() + timedelta(
                    seconds=int(expires_in)
                )

            db.commit()
            db.refresh(account)

            logger.info(
                f"Refreshed token for account {account.id} ({account.platform})"
            )
            return account

        except Exception as e:
            logger.error(f"Failed to refresh token for account {account.id}: {e}")
            account.is_active = False
            db.commit()
            raise


def get_valid_access_token(db: Session, account: Account) -> str:
    """Get a valid access token, refreshing if necessary.

    For Instagram accounts, the page access token from meta_info is returned
    (used for Graph API calls). The user token is refreshed transparently
    when approaching expiry, and the page token is updated alongside it.
    """
    if account.token_expires_at:
        now = datetime.utcnow()
        # Use a larger buffer for Instagram to avoid last-minute failures
        buffer_time = timedelta(days=7) if account.platform == "instagram" else timedelta(minutes=5)
        if now + buffer_time >= account.token_expires_at:
            logger.info(f"Token expiring soon for account {account.id}, refreshing...")
            import asyncio

            account = asyncio.run(refresh_account_token(db, account))

    # For Instagram, prefer the page access token from meta_info
    if account.platform == "instagram":
        meta_info = account.meta_info or {}
        page_token = meta_info.get("access_token")
        if page_token:
            return page_token

    return decrypt_token(account.access_token_enc)
