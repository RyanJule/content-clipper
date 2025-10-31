import redis
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "api": "operational",
        "database": "unknown",
        "redis": "unknown",
        "storage": "unknown",
    }

    # Check database
    try:
        db.execute("SELECT 1")
        health_status["database"] = "operational"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["redis"] = "operational"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check MinIO
    try:
        from app.core.storage import minio_client

        minio_client.client.bucket_exists(settings.MINIO_BUCKET)
        health_status["storage"] = "operational"
    except Exception as e:
        health_status["storage"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    return health_status
