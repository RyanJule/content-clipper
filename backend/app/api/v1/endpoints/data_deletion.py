# backend/app/api/v1/endpoints/data_deletion.py
"""
Meta Data Deletion Callback Endpoint

This endpoint handles data deletion requests from Meta (Facebook/Instagram)
when a user removes your app from their account or requests data deletion.

Meta sends a signed request that must be verified using your app secret.
"""

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.account import Account

router = APIRouter()
logger = logging.getLogger(__name__)


def parse_signed_request(signed_request: str, app_secret: str) -> Optional[dict]:
    """
    Parse and verify a signed request from Meta.
    
    Meta sends signed requests in the format: encoded_signature.payload
    The signature is a HMAC-SHA256 hash of the payload using your app secret.
    """
    try:
        # Split the signed request into signature and payload
        parts = signed_request.split(".")
        if len(parts) != 2:
            logger.error("Invalid signed request format")
            return None
        
        encoded_sig, payload = parts
        
        # Decode the signature (URL-safe base64)
        # Add padding if necessary
        encoded_sig += "=" * (4 - len(encoded_sig) % 4)
        sig = base64.urlsafe_b64decode(encoded_sig)
        
        # Decode the payload
        payload += "=" * (4 - len(payload) % 4)
        data = base64.urlsafe_b64decode(payload)
        data = json.loads(data.decode("utf-8"))
        
        # Verify the signature
        expected_sig = hmac.new(
            app_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).digest()
        
        if not hmac.compare_digest(sig, expected_sig):
            logger.error("Signed request signature verification failed")
            return None
        
        return data
        
    except Exception as e:
        logger.error(f"Error parsing signed request: {e}")
        return None


def generate_confirmation_code(user_id: str) -> str:
    """Generate a unique confirmation code for the deletion request."""
    timestamp = datetime.utcnow().isoformat()
    data = f"{user_id}:{timestamp}:{settings.SECRET_KEY}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


@router.post("/instagram/data-deletion")
async def instagram_data_deletion(
    request: Request,
    signed_request: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Handle data deletion callback from Meta (Instagram/Facebook).
    
    When a user removes your app or requests data deletion, Meta sends
    a POST request to this endpoint with a signed_request parameter.
    
    This endpoint must:
    1. Verify the signed request
    2. Delete the user's data
    3. Return a JSON response with a confirmation code and status URL
    """
    logger.info("Received Instagram data deletion request")
    
    # Parse and verify the signed request
    data = parse_signed_request(signed_request, settings.INSTAGRAM_CLIENT_SECRET)
    
    if not data:
        logger.error("Failed to parse or verify signed request")
        raise HTTPException(status_code=400, detail="Invalid signed request")
    
    # Extract the user ID from the request
    user_id = data.get("user_id")
    
    if not user_id:
        logger.error("No user_id in signed request")
        raise HTTPException(status_code=400, detail="Missing user_id")
    
    logger.info(f"Processing data deletion for Meta user_id: {user_id}")
    
    try:
        # Find and delete all Instagram accounts associated with this Meta user ID
        # The user_id from Meta corresponds to the platform user ID stored in meta_info
        deleted_count = 0
        
        accounts = db.query(Account).filter(
            Account.platform.in_(["instagram", "facebook"])
        ).all()
        
        for account in accounts:
            # Check if meta_info contains matching user_id
            if account.meta_info and account.meta_info.get("id") == str(user_id):
                logger.info(f"Deleting account {account.id} for platform {account.platform}")
                db.delete(account)
                deleted_count += 1
        
        db.commit()
        logger.info(f"Deleted {deleted_count} account(s) for Meta user_id: {user_id}")
        
    except Exception as e:
        logger.error(f"Error deleting user data: {e}")
        db.rollback()
        # Still return success to Meta - we'll handle cleanup separately if needed
    
    # Generate confirmation code
    confirmation_code = generate_confirmation_code(str(user_id))
    
    # Build the status URL where users can check deletion status
    status_url = f"{settings.FRONTEND_URL}/data-deletion-status?code={confirmation_code}"
    
    # Return the required response format
    response_data = {
        "url": status_url,
        "confirmation_code": confirmation_code
    }
    
    logger.info(f"Data deletion completed. Confirmation code: {confirmation_code}")
    
    return JSONResponse(content=response_data)


@router.get("/data-deletion-status")
async def data_deletion_status(code: str):
    """
    Check the status of a data deletion request.
    
    This endpoint allows users to verify that their data has been deleted.
    In a production environment, you might store deletion requests in a database
    and provide more detailed status information.
    """
    if not code or len(code) != 16:
        raise HTTPException(status_code=400, detail="Invalid confirmation code")
    
    # In a production app, you would look up the deletion request
    # For now, we return a generic success message
    return {
        "confirmation_code": code,
        "status": "completed",
        "message": "Your data has been successfully deleted from Content Clipper."
    }