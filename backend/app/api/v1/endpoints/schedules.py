from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.account import Account
from app.models.schedule import ContentSchedule as ScheduleModel
from app.models.schedule import ScheduledPost as ScheduledPostModel
from app.models.user import User
from app.schemas.schedule import (
    CalendarDay,
    ContentSchedule,
    ContentScheduleCreate,
    ContentScheduleUpdate,
    ScheduledPost,
    ScheduledPostCreate,
    ScheduledPostUpdate,
    ScheduleSuggestion,
)

router = APIRouter()

# ===== SCHEDULES =====


@router.post("/", response_model=ContentSchedule, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule: ContentScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new content schedule"""
    # Verify account belongs to user
    account = (
        db.query(Account)
        .filter(Account.id == schedule.account_id, Account.user_id == current_user.id)
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    db_schedule = ScheduleModel(user_id=current_user.id, **schedule.model_dump())

    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


@router.get("/", response_model=List[ContentSchedule])
async def list_schedules(
    account_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all schedules"""
    query = db.query(ScheduleModel).filter(ScheduleModel.user_id == current_user.id)

    if account_id:
        query = query.filter(ScheduleModel.account_id == account_id)

    return query.all()


@router.get("/suggestions", response_model=List[ScheduleSuggestion])
async def get_schedule_suggestions(
    platform: str, current_user: User = Depends(get_current_active_user)
):
    """Get AI-suggested posting schedules"""
    # TODO: Implement AI-based suggestions
    suggestions = [
        ScheduleSuggestion(
            name="High Engagement Schedule",
            description="Post 3 times daily during peak engagement hours",
            days_of_week=[0, 1, 2, 3, 4],  # Mon-Fri
            posting_times=["09:00", "13:00", "18:00"],
            estimated_engagement=85,
            estimated_growth=12,
            reasoning="Based on platform analytics, these times show 40% higher engagement",
        ),
        ScheduleSuggestion(
            name="Consistent Growth",
            description="Daily posting for steady audience building",
            days_of_week=[0, 1, 2, 3, 4, 5, 6],  # Every day
            posting_times=["10:00", "16:00"],
            estimated_engagement=75,
            estimated_growth=18,
            reasoning="Consistent daily content builds stronger audience relationships",
        ),
        ScheduleSuggestion(
            name="Weekend Warrior",
            description="Focus on weekend when audience is most active",
            days_of_week=[5, 6],  # Sat-Sun
            posting_times=["11:00", "15:00", "19:00"],
            estimated_engagement=90,
            estimated_growth=8,
            reasoning="Weekend posts get 50% more views but lower overall reach",
        ),
    ]

    return suggestions


@router.get("/{schedule_id}", response_model=ContentSchedule)
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific schedule"""
    schedule = (
        db.query(ScheduleModel)
        .filter(
            ScheduleModel.id == schedule_id, ScheduleModel.user_id == current_user.id
        )
        .first()
    )

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return schedule


@router.put("/{schedule_id}", response_model=ContentSchedule)
async def update_schedule(
    schedule_id: int,
    schedule_update: ContentScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a schedule"""
    schedule = (
        db.query(ScheduleModel)
        .filter(
            ScheduleModel.id == schedule_id, ScheduleModel.user_id == current_user.id
        )
        .first()
    )

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    update_data = schedule_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a schedule"""
    schedule = (
        db.query(ScheduleModel)
        .filter(
            ScheduleModel.id == schedule_id, ScheduleModel.user_id == current_user.id
        )
        .first()
    )

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(schedule)
    db.commit()
    return None


# ===== SCHEDULED POSTS =====


@router.get("/calendar/{year}/{month}", response_model=List[CalendarDay])
async def get_calendar_view(
    year: int,
    month: int,
    account_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get calendar view of scheduled posts for a month"""
    from calendar import monthrange

    # Get all days in month
    days_in_month = monthrange(year, month)[1]
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, days_in_month, 23, 59, 59)

    # Get all scheduled posts for the month
    query = db.query(ScheduledPostModel).filter(
        ScheduledPostModel.user_id == current_user.id,
        ScheduledPostModel.scheduled_for >= start_date,
        ScheduledPostModel.scheduled_for <= end_date,
    )

    if account_id:
        query = query.join(ScheduleModel).filter(ScheduleModel.account_id == account_id)

    posts = query.all()

    # Group by day
    calendar_days = []
    for day in range(1, days_in_month + 1):
        day_date = datetime(year, month, day)
        day_posts = [p for p in posts if p.scheduled_for.date() == day_date.date()]

        calendar_days.append(
            CalendarDay(
                date=day_date.strftime("%Y-%m-%d"),
                posts_needed=len(day_posts),  # TODO: Calculate from schedule
                posts_ready=len([p for p in day_posts if p.status == "content_ready"]),
                posts_scheduled=len([p for p in day_posts if p.status == "scheduled"]),
                posts=day_posts,
            )
        )

    return calendar_days


@router.post(
    "/posts", response_model=ScheduledPost, status_code=status.HTTP_201_CREATED
)
async def create_scheduled_post(
    post: ScheduledPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a scheduled post"""
    # Verify schedule belongs to user
    schedule = (
        db.query(ScheduleModel)
        .filter(
            ScheduleModel.id == post.schedule_id,
            ScheduleModel.user_id == current_user.id,
        )
        .first()
    )

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db_post = ScheduledPostModel(user_id=current_user.id, **post.model_dump())

    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@router.get("/posts/{post_id}", response_model=ScheduledPost)
async def get_scheduled_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific scheduled post"""
    post = (
        db.query(ScheduledPostModel)
        .filter(
            ScheduledPostModel.id == post_id,
            ScheduledPostModel.user_id == current_user.id,
        )
        .first()
    )

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


@router.put("/posts/{post_id}", response_model=ScheduledPost)
async def update_scheduled_post(
    post_id: int,
    post_update: ScheduledPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a scheduled post"""
    post = (
        db.query(ScheduledPostModel)
        .filter(
            ScheduledPostModel.id == post_id,
            ScheduledPostModel.user_id == current_user.id,
        )
        .first()
    )

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    update_data = post_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a scheduled post"""
    post = (
        db.query(ScheduledPostModel)
        .filter(
            ScheduledPostModel.id == post_id,
            ScheduledPostModel.user_id == current_user.id,
        )
        .first()
    )

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()
    return None
