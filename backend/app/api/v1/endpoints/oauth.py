# backend/app/api/v1/endpoints/oauth.py
import json
import secrets
from typing import Optional

import redis
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.oauth_service import get_oauth_provider, save_oauth_tokens

router = APIRouter()

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


@router.get("/debug/config")
async def debug_oauth_config():
    """
    Debug endpoint to check OAuth configuration without exposing secrets.
    Returns masked values to verify configuration is loaded correctly.
    """
    def mask_value(value: str, show_chars: int = 4) -> str:
        """Show first and last N characters, mask the middle"""
        if not value:
            return "NOT SET"
        if len(value) <= show_chars * 2:
            return f"{value[:2]}...{value[-2:]}"
        return f"{value[:show_chars]}...{value[-show_chars:]}"

    return {
        "environment": settings.ENVIRONMENT,
        "backend_url": settings.BACKEND_URL,
        "frontend_url": settings.FRONTEND_URL,
        "instagram": {
            "client_id": mask_value(settings.INSTAGRAM_CLIENT_ID) if settings.INSTAGRAM_CLIENT_ID else "NOT SET",
            "client_id_length": len(settings.INSTAGRAM_CLIENT_ID) if settings.INSTAGRAM_CLIENT_ID else 0,
            "client_secret": "SET" if settings.INSTAGRAM_CLIENT_SECRET else "NOT SET",
            "client_secret_length": len(settings.INSTAGRAM_CLIENT_SECRET) if settings.INSTAGRAM_CLIENT_SECRET else 0,
        },
        "youtube": {
            "client_id": "SET" if settings.YOUTUBE_CLIENT_ID else "NOT SET",
            "client_secret": "SET" if settings.YOUTUBE_CLIENT_SECRET else "NOT SET",
        },
        "linkedin": {
            "client_id": "SET" if settings.LINKEDIN_CLIENT_ID else "NOT SET",
            "client_secret": "SET" if settings.LINKEDIN_CLIENT_SECRET else "NOT SET",
        },
        "note": "This is a debug endpoint. Secrets are masked for security."
    }



def store_oauth_state(state: str, data: dict, expire: int = 600):
    """Store OAuth state in Redis with 10 minute expiration"""
    redis_client.setex(f"oauth_state:{state}", expire, json.dumps(data))


def get_oauth_state(state: str) -> Optional[dict]:
    """Retrieve and delete OAuth state from Redis (one-time use)"""
    key = f"oauth_state:{state}"
    data = redis_client.get(key)
    if data:
        redis_client.delete(key)
        return json.loads(data)
    return None


@router.get("/{platform}/authorize")
async def oauth_authorize(
    platform: str, current_user: User = Depends(get_current_active_user)
):
    """Initiate OAuth flow - returns authorization URL"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        provider = get_oauth_provider(platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate secure state token
    state = secrets.token_urlsafe(32)

    # Store in Redis
    store_oauth_state(state, {"user_id": current_user.id, "platform": platform})

    # Get authorization URL
    auth_url = provider.get_authorization_url(state)

    # Debug logging for Instagram OAuth
    if platform == "instagram":
        logger.info(f"Instagram OAuth Debug:")
        logger.info(f"  Client ID: {provider.client_id[:10]}...{provider.client_id[-4:]} (length: {len(provider.client_id)})")
        logger.info(f"  Authorization URL: {provider.authorization_url}")
        logger.info(f"  Redirect URI: {provider.redirect_uri}")
        logger.info(f"  Generated URL (first 150 chars): {auth_url[:150]}...")

    return {"authorization_url": auth_url, "platform": platform}


@router.get("/{platform}/callback")
async def oauth_callback(
    platform: str,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    OAuth callback endpoint - receives authorization code from provider
    Returns HTML with JavaScript to communicate with parent window
    """
    import logging

    logger = logging.getLogger(__name__)

    # Get frontend URL for postMessage origin
    frontend_origin = settings.FRONTEND_URL

    # Handle error from OAuth provider
    if error:
        error_msg = error_description or error
        logger.error(f"OAuth provider error: {error_msg}")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
        <script>
            console.log('Sending error message to parent');
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'OAUTH_ERROR',
                    error: '{error_msg}'
                }}, '{frontend_origin}');
                setTimeout(() => window.close(), 100);
            }} else {{
                window.location.href = '{frontend_origin}/accounts?error={error_msg}';
            }}
        </script>
        <p>Authorization failed. This window will close automatically.</p>
        </body>
        </html>
        """
        return HTMLResponse(html_content)

    # Validate required parameters
    if not code or not state:
        missing = "code" if not code else "state"
        logger.error(f"Missing OAuth parameter: {missing}")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
        <script>
            console.log('Sending missing parameter error to parent');
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'OAUTH_ERROR',
                    error: 'Missing {missing} parameter'
                }}, '{frontend_origin}');
                setTimeout(() => window.close(), 100);
            }} else {{
                window.location.href = '{frontend_origin}/accounts?error=missing_{missing}';
            }}
        </script>
        <p>Authorization incomplete. This window will close automatically.</p>
        </body>
        </html>
        """
        return HTMLResponse(html_content)

    # Validate state token
    state_data = get_oauth_state(state)
    if not state_data:
        logger.error(f"Invalid or expired state token: {state}")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
        <script>
            console.log('Sending invalid state error to parent');
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'OAUTH_ERROR',
                    error: 'Invalid or expired session'
                }}, '{frontend_origin}');
                setTimeout(() => window.close(), 100);
            }} else {{
                window.location.href = '{frontend_origin}/accounts?error=invalid_state';
            }}
        </script>
        <p>Session expired. Please try again.</p>
        </body>
        </html>
        """
        return HTMLResponse(html_content)

    # Exchange code for tokens
    try:
        logger.info(f"Exchanging OAuth code for {platform}")

        provider = get_oauth_provider(platform)
        token_data = await provider.exchange_code_for_token(code)

        # Get user info from platform
        access_token = token_data.get("access_token")
        user_info = await provider.get_user_info(access_token)

        logger.info(f"Got user info for {platform}: {user_info.get('username')}")

        # Save to database
        await save_oauth_tokens(
            db=db,
            user_id=state_data["user_id"],
            platform=platform,
            token_data=token_data,
            user_info=user_info,
        )

        logger.info(
            f"Successfully connected {platform} for user {state_data['user_id']}"
        )

        # Return success HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Success</title></head>
        <body>
        <script>
            console.log('Sending success message to parent');
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'OAUTH_SUCCESS',
                    platform: '{platform}'
                }}, '{frontend_origin}');
                setTimeout(() => window.close(), 100);
            }} else {{
                window.location.href = '{frontend_origin}/accounts?success=true&platform={platform}';
            }}
        </script>
        <div style="text-align: center; padding: 40px; font-family: sans-serif;">
            <h2>✓ Connected Successfully!</h2>
            <p>Your {platform} account has been connected.</p>
            <p style="color: #666;">This window will close automatically...</p>
        </div>
        </body>
        </html>
        """
        return HTMLResponse(html_content)

    except Exception as e:
        logger.error(f"OAuth callback error for {platform}: {e}", exc_info=True)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
        <script>
            console.log('Sending connection failed error to parent');
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'OAUTH_ERROR',
                    error: 'Failed to connect account'
                }}, '{frontend_origin}');
                setTimeout(() => window.close(), 100);
            }} else {{
                window.location.href = '{frontend_origin}/accounts?error=connection_failed';
            }}
        </script>
        <p>Connection failed. Please try again.</p>
        </body>
        </html>
        """
        return HTMLResponse(html_content)


@router.post("/{platform}/disconnect")
async def oauth_disconnect(
    platform: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Disconnect a connected OAuth account"""
    from app.models.account import Account as AccountModel

    account = (
        db.query(AccountModel)
        .filter(
            AccountModel.user_id == current_user.id,
            AccountModel.platform == platform,
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(account)
    db.commit()

    return {"message": f"{platform} account disconnected successfully"}


@router.get("/{platform}/status")
async def oauth_status(
    platform: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Check OAuth connection status for a platform"""
    from datetime import datetime

    from app.models.account import Account as AccountModel

    account = (
        db.query(AccountModel)
        .filter(
            AccountModel.user_id == current_user.id,
            AccountModel.platform == platform,
        )
        .first()
    )

    if not account:
        return {"connected": False, "platform": platform}

    # Check token expiration
    is_expired = False
    if account.token_expires_at:
        is_expired = datetime.utcnow() >= account.token_expires_at

    return {
        "connected": True,
        "platform": platform,
        "account_username": account.account_username,
        "is_active": account.is_active,
        "is_expired": is_expired,
        "connected_at": account.connected_at,
        "token_expires_at": account.token_expires_at,
    }


@router.get("/instagram/available-accounts")
async def get_available_instagram_accounts(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get list of available Instagram Business accounts from user's Facebook Pages.

    This endpoint is used during the OAuth flow to allow users to select
    which Instagram account to connect if they have multiple options.

    Permissions used:
    - pages_show_list: Lists Facebook Pages
    - instagram_business_basic: Gets Instagram account info

    Note: This requires a valid Facebook access token. Should be called
    during or after the OAuth flow.
    """
    from app.services.oauth_service import get_oauth_provider
    from app.models.account import Account as AccountModel
    from app.core.crypto import decrypt_token

    # Check if user has a connected Instagram account to get access token
    # In a real implementation, you'd need to handle the OAuth flow first
    # This is a placeholder for the app review documentation

    # For now, return an informative message
    return {
        "message": "This endpoint is called during OAuth flow",
        "instructions": [
            "Complete OAuth authorization first",
            "This will provide access to your Facebook Pages",
            "Pages with Instagram Business accounts will be listed",
            "Select the account you want to connect"
        ],
        "note": "This endpoint demonstrates the pages_show_list and instagram_business_basic permissions"
    }
