from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.account import Account


class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = None


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = None


class Brand(BrandBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    accounts: List[Account] = []

    class Config:
        from_attributes = True
