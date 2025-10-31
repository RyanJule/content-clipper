import logging
from typing import Dict, List, Optional

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None


def transcribe_audio(audio_path: str) -> Optional[Dict]:
    """Transcribe audio using OpenAI Whisper"""
    if not client:
        logger.error("OpenAI API key not configured")
        return None

    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="verbose_json"
            )

        return {
            "text": transcript.text,
            "segments": transcript.segments if hasattr(transcript, "segments") else [],
            "language": (
                transcript.language if hasattr(transcript, "language") else "en"
            ),
        }

    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return None


def generate_clip_title(transcription: str, context: str = "") -> Optional[str]:
    """Generate a title for a clip using GPT"""
    if not client:
        logger.error("OpenAI API key not configured")
        return None

    try:
        prompt = f"""Generate a short, catchy title (max 60 characters) for a video clip based on this transcription:

Transcription: {transcription[:500]}

Context: {context}

Title:"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media content expert who creates engaging video titles.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=50,
            temperature=0.7,
        )

        title = response.choices[0].message.content.strip()
        return title

    except Exception as e:
        logger.error(f"Error generating title: {e}")
        return None


def generate_clip_description(transcription: str, title: str = "") -> Optional[str]:
    """Generate a description for a clip using GPT"""
    if not client:
        logger.error("OpenAI API key not configured")
        return None

    try:
        prompt = f"""Generate an engaging description (2-3 sentences, max 200 characters) for a video clip:

Title: {title}
Transcription: {transcription[:500]}

Description:"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media content expert who creates engaging video descriptions.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.7,
        )

        description = response.choices[0].message.content.strip()
        return description

    except Exception as e:
        logger.error(f"Error generating description: {e}")
        return None


def generate_hashtags(
    transcription: str, platform: str = "general"
) -> Optional[List[str]]:
    """Generate relevant hashtags using GPT"""
    if not client:
        logger.error("OpenAI API key not configured")
        return None

    try:
        prompt = f"""Generate 5-7 relevant hashtags for a {platform} video clip based on this content:

{transcription[:500]}

Format: Return only hashtags separated by spaces, starting with #"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media expert who creates trending hashtags.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.7,
        )

        hashtags_text = response.choices[0].message.content.strip()
        hashtags = [tag.strip() for tag in hashtags_text.split() if tag.startswith("#")]
        return hashtags[:7]

    except Exception as e:
        logger.error(f"Error generating hashtags: {e}")
        return None


def suggest_clip_timestamps(
    transcription_data: Dict, target_duration: float = 60.0
) -> List[Dict]:
    """Suggest interesting clip timestamps based on transcription"""
    if not client:
        logger.error("OpenAI API key not configured")
        return []

    try:
        segments = transcription_data.get("segments", [])
        if not segments:
            return []

        full_text = " ".join([seg.get("text", "") for seg in segments])

        prompt = f"""Based on this video transcription, suggest 3 interesting moments that would make good short clips (30-90 seconds each).

Transcription: {full_text[:1000]}

For each suggestion, provide:
1. A brief reason why this moment is interesting
2. Approximate timestamp range

Format your response as JSON array with objects containing: reason, start_seconds, end_seconds"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a video editing expert who identifies engaging content moments.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        suggestions_text = response.choices[0].message.content.strip()

        import json

        suggestions = json.loads(suggestions_text)
        return suggestions

    except Exception as e:
        logger.error(f"Error suggesting timestamps: {e}")
        return []
