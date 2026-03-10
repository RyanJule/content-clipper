from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.brand import Brand as BrandModel
from app.models.account import Account as AccountModel
from app.models.user import User
from app.schemas.brand import Brand, BrandCreate, BrandUpdate

router = APIRouter()


@router.post("/", response_model=Brand, status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand: BrandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new brand"""
    db_brand = BrandModel(
        user_id=current_user.id,
        name=brand.name,
        description=brand.description,
        logo_url=brand.logo_url,
    )
    db.add(db_brand)
    db.commit()
    db.refresh(db_brand)
    return db_brand


@router.get("/", response_model=List[Brand])
async def list_brands(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all brands for the current user"""
    return db.query(BrandModel).filter(BrandModel.user_id == current_user.id).all()


@router.get("/{brand_id}", response_model=Brand)
async def get_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific brand"""
    brand = (
        db.query(BrandModel)
        .filter(BrandModel.id == brand_id, BrandModel.user_id == current_user.id)
        .first()
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.put("/{brand_id}", response_model=Brand)
async def update_brand(
    brand_id: int,
    brand_update: BrandUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a brand"""
    brand = (
        db.query(BrandModel)
        .filter(BrandModel.id == brand_id, BrandModel.user_id == current_user.id)
        .first()
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    update_data = brand_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brand, field, value)

    db.commit()
    db.refresh(brand)
    return brand


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a brand (accounts are unlinked, not deleted)"""
    brand = (
        db.query(BrandModel)
        .filter(BrandModel.id == brand_id, BrandModel.user_id == current_user.id)
        .first()
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    db.delete(brand)
    db.commit()
    return None


@router.post("/{brand_id}/accounts/{account_id}", response_model=Brand)
async def assign_account_to_brand(
    brand_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Assign an existing account to a brand (one per platform per brand)"""
    brand = (
        db.query(BrandModel)
        .filter(BrandModel.id == brand_id, BrandModel.user_id == current_user.id)
        .first()
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    account = (
        db.query(AccountModel)
        .filter(AccountModel.id == account_id, AccountModel.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Enforce one account per platform per brand
    existing = (
        db.query(AccountModel)
        .filter(
            AccountModel.brand_id == brand_id,
            AccountModel.platform == account.platform,
            AccountModel.id != account_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Brand already has a {account.platform} account connected. Disconnect it first.",
        )

    account.brand_id = brand_id
    db.commit()
    db.refresh(brand)
    return brand


@router.delete("/{brand_id}/accounts/{account_id}", response_model=Brand)
async def remove_account_from_brand(
    brand_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Remove an account from a brand (account is not deleted)"""
    brand = (
        db.query(BrandModel)
        .filter(BrandModel.id == brand_id, BrandModel.user_id == current_user.id)
        .first()
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    account = (
        db.query(AccountModel)
        .filter(
            AccountModel.id == account_id,
            AccountModel.user_id == current_user.id,
            AccountModel.brand_id == brand_id,
        )
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found in this brand")

    account.brand_id = None
    db.commit()
    db.refresh(brand)
    return brand
