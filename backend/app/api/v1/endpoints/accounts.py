from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.account import Account as AccountModel
from app.models.user import User
from app.schemas.account import Account, AccountCreate, AccountUpdate

router = APIRouter()


@router.post("/", response_model=Account, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Connect a new social media account"""
    # TODO: Implement token encryption
    db_account = AccountModel(
        user_id=current_user.id,
        platform=account.platform,
        account_username=account.account_username,
        is_active=account.is_active,
        access_token_enc=account.access_token,  # TODO: Encrypt this
        refresh_token_enc=account.refresh_token,  # TODO: Encrypt this
        token_expires_at=account.token_expires_at,
        meta_info=account.meta_info,
    )

    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@router.get("/", response_model=List[Account])
async def list_accounts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """List all connected accounts"""
    accounts = (
        db.query(AccountModel).filter(AccountModel.user_id == current_user.id).all()
    )
    return accounts


@router.get("/{account_id}", response_model=Account)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific account"""
    account = (
        db.query(AccountModel)
        .filter(AccountModel.id == account_id, AccountModel.user_id == current_user.id)
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return account


@router.put("/{account_id}", response_model=Account)
async def update_account(
    account_id: int,
    account_update: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an account"""
    account = (
        db.query(AccountModel)
        .filter(AccountModel.id == account_id, AccountModel.user_id == current_user.id)
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    update_data = account_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Disconnect an account"""
    account = (
        db.query(AccountModel)
        .filter(AccountModel.id == account_id, AccountModel.user_id == current_user.id)
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(account)
    db.commit()
    return None
