# app/crud/accounts.py
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.core.crypto import decrypt_token, encrypt_token
from app.models.account import Account


def create_account(
    db: Session,
    user_id: int,
    platform: str,
    account_username: str,
    access_token: Optional[str],
    refresh_token: Optional[str],
    token_expires_at: Optional[datetime],
    metadata: Optional[Dict] = None,
) -> Account:
    """Encrypt and create an account record"""
    acc = Account(
        user_id=user_id,
        platform=platform,
        account_username=account_username,
        access_token_enc=encrypt_token(access_token),
        refresh_token_enc=encrypt_token(refresh_token),
        token_expires_at=token_expires_at,
        metadata=metadata or {},
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


def get_account(db: Session, account_id: int) -> Optional[Account]:
    return db.query(Account).filter(Account.id == account_id).first()


def get_user_accounts(db: Session, user_id: int):
    return db.query(Account).filter(Account.user_id == user_id).all()


def get_decrypted_tokens(account: Account):
    """Helper to decrypt tokens when performing actions"""
    return {
        "access_token": decrypt_token(account.access_token_enc),
        "refresh_token": decrypt_token(account.refresh_token_enc),
    }
