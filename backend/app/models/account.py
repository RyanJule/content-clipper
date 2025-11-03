# app/models/account.py
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Platform data
    platform = Column(
        String(50), nullable=False
    )  # e.g., "instagram", "twitter", "youtube"
    account_username = Column(String(255), nullable=False)

    # Encrypted tokens (Fernet-encrypted)
    access_token_enc = Column(String, nullable=True)
    refresh_token_enc = Column(String, nullable=True)

    token_expires_at = Column(DateTime, nullable=True)
    connected_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Optional metadata (profile id, scopes, etc.)
    meta_info = Column(JSON, nullable=True)

    # Relationship
    user = relationship("User", back_populates="accounts")
