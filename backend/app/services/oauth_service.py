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
    """Instagram OAuth (via Facebook Graph API)"""

    def __init__(self):
        super().__init__()
        self.platform_name = "instagram"
        self.client_id = settings.INSTAGRAM_CLIENT_ID
        self.client_secret = settings.INSTAGRAM_CLIENT_SECRET
        self.redirect_uri = f"{settings.BACKEND_URL}/api/v1/oauth/instagram/callback"
        self.authorization_url = "https://api.instagram.com/oauth/authorize"
        self.token_url = "https://api.instagram.com/oauth/access_token"
        self.scope = ["user_profile", "user_media"]

    async def get_user_info(self, access_token: str) -> Dict:
        """Get Instagram user profile"""
        url = f"https://graph.instagram.com/me?fields=id,username&access_token={access_token}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()


class YouTubeOAuth(OAuthProvider):
    """YouTube OAuth (via Google)"""

    def __init__(self):
        super().__init__()
        self.platform_name = "youtube"
        self.client_id = settings.YOUTUBE_CLIENT_ID
        self.client_secret = settings.YOUTUBE_CLIENT_SECRET
        self.redirect_uri = f"{settings.BACKEND_URL}/api/v1/oauth/youtube/callback"
        self.authorization_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.scope = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
        ]

    def get_authorization_url(self, state: str) -> str:
        """Override to add access_type and prompt"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scope),
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent screen
        }
        return f"{self.authorization_url}?{urlencode(params)}"

    async def get_user_info(self, access_token: str) -> Dict:
        """Get YouTube channel info"""
        url = "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get("items"):
                channel = data["items"][0]
                return {
                    "id": channel["id"],
                    "username": channel["snippet"]["title"],
                }
            return {}


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
        """TikTok token exchange"""
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
            return response.json()

    async def get_user_info(self, access_token: str) -> Dict:
        """Get TikTok user info"""
        url = "https://open.tiktokapis.com/v2/user/info/?fields=open_id,display_name"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            user_data = data.get("data", {}).get("user", {})
            return {
                "id": user_data.get("open_id"),
                "username": user_data.get("display_name"),
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
    """Refresh an expired access token"""
    provider = get_oauth_provider(account.platform)

    refresh_token = decrypt_token(account.refresh_token_enc)
    if not refresh_token:
        raise ValueError("No refresh token available")

    try:
        token_data = await provider.refresh_access_token(refresh_token)

        # Update account with new tokens
        account.access_token_enc = encrypt_token(token_data.get("access_token"))

        # Some providers return a new refresh token
        if token_data.get("refresh_token"):
            account.refresh_token_enc = encrypt_token(token_data["refresh_token"])

        # Update expiration
        expires_in = token_data.get("expires_in")
        if expires_in:
            account.token_expires_at = datetime.utcnow() + timedelta(
                seconds=int(expires_in)
            )

        db.commit()
        db.refresh(account)

        logger.info(f"Refreshed token for account {account.id} ({account.platform})")
        return account

    except Exception as e:
        logger.error(f"Failed to refresh token for account {account.id}: {e}")
        account.is_active = False
        db.commit()
        raise


def get_valid_access_token(db: Session, account: Account) -> str:
    """Get a valid access token, refreshing if necessary"""
    # Check if token is expired or about to expire (within 5 minutes)
    if account.token_expires_at:
        now = datetime.utcnow()
        buffer_time = timedelta(minutes=5)
        if now + buffer_time >= account.token_expires_at:
            logger.info(f"Token expired for account {account.id}, refreshing...")
            import asyncio

            account = asyncio.run(refresh_account_token(db, account))

    return decrypt_token(account.access_token_enc)
