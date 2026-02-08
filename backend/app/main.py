from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1 import api_router
from app.core.config import settings

app = FastAPI(
    title="Content Clipper API",
    description="AI-powered video/audio clipping and social media scheduler",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

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
