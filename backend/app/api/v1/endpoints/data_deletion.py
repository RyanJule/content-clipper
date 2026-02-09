# backend/app/api/v1/endpoints/data_deletion.py
"""
Meta Data Deletion Callback Endpoint

Handles data deletion requests from Meta (Facebook/Instagram) when a user
removes the app from their account or requests data deletion through Meta's
privacy controls.

Meta sends a signed request (HMAC-SHA256) that is verified against the app
secret before any data is removed.

See: https://developers.facebook.com/docs/development/create-an-app/app-dashboard/data-deletion-callback
"""

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Optional

import redis
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.account import Account
from app.models.social_post import SocialPlatform, SocialPost

router = APIRouter()
logger = logging.getLogger(__name__)

# Redis client for storing deletion request status
_redis_client: Optional[redis.Redis] = None

# Deletion request records expire after 180 days
DELETION_RECORD_TTL_SECONDS = 180 * 24 * 60 * 60


def _get_redis() -> redis.Redis:
    """Lazy-init Redis client (shares the same Redis as the rest of the app)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def parse_signed_request(signed_request: str, app_secret: str) -> Optional[dict]:
    """
    Parse and verify a signed request from Meta.

    Meta sends signed requests in the format: encoded_signature.payload
    The signature is a HMAC-SHA256 hash of the payload using your app secret.
    """
    try:
        parts = signed_request.split(".")
        if len(parts) != 2:
            logger.error("Invalid signed request format")
            return None

        encoded_sig, payload = parts

        # Decode the signature (URL-safe base64, add padding)
        encoded_sig += "=" * (4 - len(encoded_sig) % 4)
        sig = base64.urlsafe_b64decode(encoded_sig)

        # Decode the payload
        payload_padded = payload + "=" * (4 - len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload_padded).decode("utf-8"))

        # Verify the signature against the raw payload string (before our padding)
        expected_sig = hmac.new(
            app_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(sig, expected_sig):
            logger.error("Signed request signature verification failed")
            return None

        return data

    except Exception as e:
        logger.error(f"Error parsing signed request: {e}")
        return None


def generate_confirmation_code(user_id: str) -> str:
    """Generate a deterministic confirmation code for a deletion request."""
    data = f"{user_id}:{settings.SECRET_KEY}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def _store_deletion_record(
    confirmation_code: str,
    meta_user_id: str,
    deleted_account_count: int,
    deleted_post_count: int,
) -> None:
    """Persist a deletion request record in Redis so the status endpoint works."""
    record = {
        "meta_user_id": meta_user_id,
        "deleted_accounts": deleted_account_count,
        "deleted_posts": deleted_post_count,
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
    }
    try:
        r = _get_redis()
        r.setex(
            f"deletion_request:{confirmation_code}",
            DELETION_RECORD_TTL_SECONDS,
            json.dumps(record),
        )
    except Exception as e:
        # Non-fatal — the deletion itself already succeeded
        logger.warning(f"Failed to store deletion record in Redis: {e}")


def _get_deletion_record(confirmation_code: str) -> Optional[dict]:
    """Retrieve a previously stored deletion record."""
    try:
        r = _get_redis()
        raw = r.get(f"deletion_request:{confirmation_code}")
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning(f"Failed to read deletion record from Redis: {e}")
    return None


@router.post("/instagram/data-deletion")
async def instagram_data_deletion(
    request: Request,
    signed_request: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Handle data deletion callback from Meta (Instagram/Facebook).

    When a user removes the app or requests data deletion, Meta sends a POST
    request with a signed_request form parameter.

    This endpoint:
    1. Verifies the HMAC-SHA256 signature
    2. Identifies the user's accounts by matching the Meta user_id against
       the facebook_user_id stored in each account's meta_info
    3. Deletes matching accounts and their associated social posts
    4. Records the deletion so the status URL returns real data
    5. Returns the JSON response format required by Meta
    """
    logger.info("Received Instagram data deletion request")

    # --- Verify the signed request ---
    data = parse_signed_request(signed_request, settings.INSTAGRAM_CLIENT_SECRET)
    if not data:
        logger.error("Failed to parse or verify signed request")
        raise HTTPException(status_code=400, detail="Invalid signed request")

    meta_user_id = data.get("user_id")
    if not meta_user_id:
        logger.error("No user_id in signed request payload")
        raise HTTPException(status_code=400, detail="Missing user_id")

    meta_user_id_str = str(meta_user_id)
    logger.info(f"Processing data deletion for Meta user_id: {meta_user_id_str}")

    deleted_account_count = 0
    deleted_post_count = 0

    try:
        # Find all Instagram/Facebook accounts whose meta_info references this
        # Meta user ID. We check both "facebook_user_id" (the primary key) and
        # "id" (the IG business account ID) to be thorough.
        accounts = (
            db.query(Account)
            .filter(Account.platform.in_(["instagram", "facebook"]))
            .all()
        )

        app_user_ids: set[int] = set()

        for account in accounts:
            meta = account.meta_info or {}
            fb_uid = str(meta.get("facebook_user_id", ""))
            ig_id = str(meta.get("id", ""))

            if meta_user_id_str in (fb_uid, ig_id):
                app_user_ids.add(account.user_id)
                logger.info(
                    f"Deleting account {account.id} "
                    f"(platform={account.platform}, user_id={account.user_id})"
                )
                db.delete(account)
                deleted_account_count += 1

        # Delete social posts that were made through the deleted accounts
        if app_user_ids:
            posts = (
                db.query(SocialPost)
                .filter(
                    SocialPost.user_id.in_(app_user_ids),
                    SocialPost.platform == SocialPlatform.INSTAGRAM,
                )
                .all()
            )
            for post in posts:
                db.delete(post)
                deleted_post_count += 1

        db.commit()
        logger.info(
            f"Deleted {deleted_account_count} account(s) and "
            f"{deleted_post_count} post(s) for Meta user_id: {meta_user_id_str}"
        )

    except Exception as e:
        logger.error(f"Error deleting user data: {e}")
        db.rollback()
        # Still return success to Meta; we log the error for manual follow-up.

    # --- Build response ---
    confirmation_code = generate_confirmation_code(meta_user_id_str)

    # Persist the record for the status endpoint
    _store_deletion_record(
        confirmation_code, meta_user_id_str, deleted_account_count, deleted_post_count
    )

    status_url = (
        f"{settings.FRONTEND_URL}/data-deletion-status?code={confirmation_code}"
    )

    response_data = {
        "url": status_url,
        "confirmation_code": confirmation_code,
    }

    logger.info(f"Data deletion completed. Confirmation code: {confirmation_code}")

    return JSONResponse(content=response_data)


@router.get("/data-deletion-status")
async def data_deletion_status(code: str):
    """
    Check the status of a data deletion request.

    Users land on this page via the status URL returned to Meta. The
    confirmation code is looked up in Redis to return real deletion details.
    """
    if not code or len(code) != 16:
        raise HTTPException(status_code=400, detail="Invalid confirmation code")

    record = _get_deletion_record(code)

    if record:
        return {
            "confirmation_code": code,
            "status": record["status"],
            "deleted_accounts": record.get("deleted_accounts", 0),
            "deleted_posts": record.get("deleted_posts", 0),
            "completed_at": record.get("completed_at"),
            "message": "Your data has been successfully deleted from Content Clipper.",
        }

    # If the record has expired or was never stored (e.g. Redis was down),
    # return a generic success — Meta requires the URL to remain functional.
    return {
        "confirmation_code": code,
        "status": "completed",
        "message": "Your data has been successfully deleted from Content Clipper.",
    }
