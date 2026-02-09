import os
from pathlib import Path
from typing import Optional


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()


def is_video_file(filename: str) -> bool:
    """Check if file is a video"""
    video_extensions = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"]
    return get_file_extension(filename) in video_extensions


def is_audio_file(filename: str) -> bool:
    """Check if file is audio"""
    audio_extensions = [".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg", ".wma"]
    return get_file_extension(filename) in audio_extensions


def is_image_file(filename: str) -> bool:
    """Check if file is an image"""
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
    return get_file_extension(filename) in image_extensions


def ensure_directory_exists(directory: str) -> Path:
    """Ensure a directory exists, create if it doesn't"""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB"""
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)
