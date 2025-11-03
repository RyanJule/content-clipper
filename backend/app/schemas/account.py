# app/schemas/account.py
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    platform: str = Field(
        ..., description="Platform name (e.g. instagram, youtube, tiktok)"
    )
    account_username: str = Field(
        ..., description="The username or handle of the connected account"
    )
    is_active: bool = True


class AccountCreate(AccountBase):
    access_token: Optional[str] = Field(
        None, description="Access token returned by OAuth"
    )
    refresh_token: Optional[str] = Field(None, description="Refresh token if provided")
    token_expires_at: Optional[datetime] = None
    meta_info: Optional[Dict] = Field(
        None, description="Any additional metadata from OAuth provider"
    )


class AccountUpdate(BaseModel):
    is_active: Optional[bool] = None
    meta_info: Optional[Dict] = None


class Account(AccountBase):
    id: int
    connected_at: datetime
    token_expires_at: Optional[datetime] = None
    meta_info: Optional[Dict] = None

    class Config:
        from_attributes = True
