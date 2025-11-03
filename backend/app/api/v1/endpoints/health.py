import logging

import redis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
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

    overall_healthy = True

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["database"] = "operational"
        logger.info("Database check: OK")
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
        overall_healthy = False
        logger.error(f"Database check failed: {e}")

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=5)
        r.ping()
        health_status["redis"] = "operational"
        logger.info("Redis check: OK")
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
        overall_healthy = False
        logger.error(f"Redis check failed: {e}")

    # Check MinIO
    try:
        from app.core.storage import minio_client

        exists = minio_client.client.bucket_exists(settings.MINIO_BUCKET)
        if exists:
            health_status["storage"] = "operational"
            logger.info("MinIO check: OK")
        else:
            health_status["storage"] = "bucket not found"
            health_status["status"] = "degraded"
            overall_healthy = False
    except Exception as e:
        health_status["storage"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
        overall_healthy = False
        logger.error(f"MinIO check failed: {e}")

    if overall_healthy:
        health_status["status"] = "healthy"

    return health_status
