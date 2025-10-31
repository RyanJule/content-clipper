import json
import logging
import subprocess
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def get_video_metadata(video_path: str) -> Optional[Dict]:
    """Extract video metadata using FFprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            logger.error(f"FFprobe error: {result.stderr}")
            return None

    except Exception as e:
        logger.error(f"Error getting video metadata: {e}")
        return None


def extract_clip(
    input_path: str, output_path: str, start_time: float, end_time: float
) -> bool:
    """Extract a clip from video using FFmpeg"""
    try:
        duration = end_time - start_time

        cmd = [
            "ffmpeg",
            "-i",
            input_path,
            "-ss",
            str(start_time),
            "-t",
            str(duration),
            "-c",
            "copy",
            "-y",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"Clip extracted successfully: {output_path}")
            return True
        else:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error extracting clip: {e}")
        return False


def get_video_duration(video_path: str) -> Optional[float]:
    """Get video duration in seconds"""
    metadata = get_video_metadata(video_path)

    if metadata and "format" in metadata:
        duration = metadata["format"].get("duration")
        return float(duration) if duration else None

    return None


def get_video_resolution(video_path: str) -> Optional[tuple]:
    """Get video resolution (width, height)"""
    metadata = get_video_metadata(video_path)

    if metadata and "streams" in metadata:
        for stream in metadata["streams"]:
            if stream.get("codec_type") == "video":
                width = stream.get("width")
                height = stream.get("height")
                if width and height:
                    return (width, height)

    return None


def extract_audio_from_video(video_path: str, audio_path: str) -> bool:
    """Extract audio track from video"""
    try:
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-y",
            audio_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"Audio extracted successfully: {audio_path}")
            return True
        else:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        return False


def generate_thumbnail(
    video_path: str, thumbnail_path: str, timestamp: float = 1.0
) -> bool:
    """Generate thumbnail from video at specified timestamp"""
    try:
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-ss",
            str(timestamp),
            "-vframes",
            "1",
            "-q:v",
            "2",
            "-y",
            thumbnail_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"Thumbnail generated successfully: {thumbnail_path}")
            return True
        else:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        return False
