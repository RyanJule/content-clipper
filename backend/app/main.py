import json
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1 import api_router
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Content Clipper API",
    description="AI-powered video/audio clipping and social media scheduler",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


class JsonBodyLoggingMiddleware(BaseHTTPMiddleware):
    """Log the JSON body of incoming requests."""

    async def dispatch(self, request: Request, call_next):
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body_bytes = await request.body()
                body = json.loads(body_bytes)
                logger.info(
                    "Request %s %s body: %s",
                    request.method,
                    request.url.path,
                    json.dumps(body),
                )
                # Restore the body stream so downstream handlers can read it.
                # request.body() drains the ASGI receive channel; without this,
                # endpoint handlers hang waiting for body bytes that never arrive.
                async def receive():
                    return {"type": "http.request", "body": body_bytes, "more_body": False}

                request = Request(request.scope, receive)
            except Exception:
                pass
        return await call_next(request)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# JSON body logging middleware
app.add_middleware(JsonBodyLoggingMiddleware)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Content Clipper API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy"}
