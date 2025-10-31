from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.social_post import SocialPost, SocialPostCreate, SocialPostUpdate
from app.services import social_service

router = APIRouter()


@router.post("/", response_model=SocialPost, status_code=status.HTTP_201_CREATED)
async def create_social_post(
    post: SocialPostCreate, user_id: int = 1, db: Session = Depends(get_db)
):
    """Create a new social media post"""
    try:
        return social_service.create_social_post(db, post=post, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[SocialPost])
async def list_social_posts(
    skip: int = 0, limit: int = 100, user_id: int = 1, db: Session = Depends(get_db)
):
    """List all social posts for a user"""
    posts = social_service.get_user_posts(db, user_id=user_id, skip=skip, limit=limit)
    return posts


@router.get("/{post_id}", response_model=SocialPost)
async def get_social_post(post_id: int, db: Session = Depends(get_db)):
    """Get a specific social post"""
    post = social_service.get_post(db, post_id=post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


@router.put("/{post_id}", response_model=SocialPost)
async def update_social_post(
    post_id: int, post: SocialPostUpdate, db: Session = Depends(get_db)
):
    """Update a social post"""
    db_post = social_service.update_post(db, post_id=post_id, post=post)
    if db_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return db_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_social_post(post_id: int, db: Session = Depends(get_db)):
    """Delete a social post"""
    success = social_service.delete_post(db, post_id=post_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return None


@router.post("/{post_id}/publish")
async def publish_social_post(post_id: int, db: Session = Depends(get_db)):
    """Publish a social post immediately"""
    try:
        result = social_service.publish_post(db, post_id=post_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
