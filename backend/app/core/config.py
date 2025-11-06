# backend/app/core/config.py
import secrets
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # URLs
    BACKEND_URL: str = "https://www.machine-systems.org"
    FRONTEND_URL: str = "https://www.machine-systems.org"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FERNET_KEY: str = ""

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET: str = "clipper-media"
    MINIO_SECURE: bool = False

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Instagram OAuth (via Facebook)
    INSTAGRAM_CLIENT_ID: str = ""
    INSTAGRAM_CLIENT_SECRET: str = ""

    # YouTube OAuth (via Google)
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""

    # LinkedIn OAuth
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""

    # TikTok OAuth
    TIKTOK_CLIENT_KEY: str = ""
    TIKTOK_CLIENT_SECRET: str = ""

    # Twitter/X OAuth
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_SECRET: str = ""

    # CORS - Allow all origins in development
    ALLOWED_ORIGINS: List[str] = ["*"]

    # File Upload
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_VIDEO_FORMATS: List[str] = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    ALLOWED_AUDIO_FORMATS: List[str] = [".mp3", ".wav", ".m4a", ".flac", ".aac"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
