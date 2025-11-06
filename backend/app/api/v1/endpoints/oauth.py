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


def store_oauth_state(state: str, data: dict, expire: int = 600):
    redis_client.setex(f"oauth_state:{state}", expire, json.dumps(data))


def get_oauth_state(state: str) -> Optional[dict]:
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
    try:
        provider = get_oauth_provider(platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    state = secrets.token_urlsafe(32)
    store_oauth_state(state, {"user_id": current_user.id, "platform": platform})
    auth_url = provider.get_authorization_url(state)
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
    import logging

    logger = logging.getLogger(__name__)

    # Handle provider error
    if error:
        html_content = f"""
        <html>
        <body>
        <script>
            if (window.opener) {{
                window.opener.postMessage({{ type: 'OAUTH_ERROR', error: '{error_description or error}' }}, window.origin);
                window.close();
            }} else {{
                window.location.href='{settings.FRONTEND_URL}/accounts?error={error_description or error}';
            }}
        </script>
        </body>
        </html>
        """
        return HTMLResponse(html_content)

    if not code or not state:
        missing = "code" if not code else "state"
        html_content = f"""
        <html>
        <body>
        <script>
            if (window.opener) {{
                window.opener.postMessage({{ type: 'OAUTH_ERROR', error: 'missing_{missing}' }}, window.origin);
                window.close();
            }} else {{
                window.location.href='{settings.FRONTEND_URL}/accounts?error=missing_{missing}';
            }}
        </script>
        </body>
        </html>
        """
        return HTMLResponse(html_content)

    state_data = get_oauth_state(state)
    if not state_data:
        html_content = f"""
        <html>
        <body>
        <script>
            if (window.opener) {{
                window.opener.postMessage({{ type: 'OAUTH_ERROR', error: 'invalid_or_expired_state' }}, window.origin);
                window.close();
            }} else {{
                window.location.href='{settings.FRONTEND_URL}/accounts?error=invalid_or_expired_state';
            }}
        </script>
        </body>
        </html>
        """
        return HTMLResponse(html_content)

    try:
        provider = get_oauth_provider(platform)
        token_data = await provider.exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        user_info = await provider.get_user_info(access_token)
        await save_oauth_tokens(
            db=db,
            user_id=state_data["user_id"],
            platform=platform,
            token_data=token_data,
            user_info=user_info,
        )

        html_content = f"""
        <html>
        <body>
        <script>
            if (window.opener) {{
                window.opener.postMessage({{ type: 'OAUTH_SUCCESS', platform: '{platform}' }}, window.origin);
                window.close();
            }} else {{
                window.location.href='{settings.FRONTEND_URL}/accounts';
            }}
        </script>
        <p>OAuth successful! You can close this window.</p>
        </body>
        </html>
        """
        return HTMLResponse(html_content)
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        html_content = f"""
        <html>
        <body>
        <script>
            if (window.opener) {{
                window.opener.postMessage({{ type: 'OAUTH_ERROR', error: 'connection_failed' }}, window.origin);
                window.close();
            }} else {{
                window.location.href='{settings.FRONTEND_URL}/accounts?error=connection_failed';
            }}
        </script>
        </body>
        </html>
        """
        return HTMLResponse(html_content)
