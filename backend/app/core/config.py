# backend/app/core/config.py
import secrets
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # URLs
    BACKEND_URL: str = "https://machine-systems.org"
    FRONTEND_URL: str = "https://machine-systems.org"

    @field_validator("BACKEND_URL", "FRONTEND_URL")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

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
    # Comma-separated list of TikTok OAuth scopes.
    # Default: Login Kit scopes only. To enable content posting, add the
    # Content Posting API scopes after approving them in the TikTok Developer Console:
    # user.info.basic,user.info.profile,video.publish,video.upload,video.list,user.info.stats
    TIKTOK_SCOPES: str = "user.info.basic,user.info.profile"

    # Twitter/X OAuth
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_SECRET: str = ""

    # CORS - Allow all origins in development
    ALLOWED_ORIGINS: List[str] = ["*"]

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024 * 1024  # 10GB
    ALLOWED_VIDEO_FORMATS: List[str] = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    ALLOWED_AUDIO_FORMATS: List[str] = [".mp3", ".wav", ".m4a", ".flac", ".aac"]
    ALLOWED_IMAGE_FORMATS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
