from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.account import Account, AccountCreate
from app.services import account_service as crud_accounts

router = APIRouter()


@router.get("/", response_model=List[Account])
def list_user_accounts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    return crud_accounts.get_user_accounts(db, current_user.id)


@router.post("/", response_model=Account)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_accounts.create_account(
        db=db,
        user_id=current_user.id,
        platform=account_data.platform,
        account_username=account_data.account_username,
        access_token=account_data.access_token,
        refresh_token=account_data.refresh_token,
        token_expires_at=account_data.token_expires_at,
        metadata=account_data.metadata,
    )
