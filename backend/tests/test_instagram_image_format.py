"""
Tests for _get_instagram_image_url format/colorspace detection.

Covers the fix for Instagram Graph API error 36001/2207083
("The image format is not supported"), which occurs when an image file's
actual format or colorspace does not match what Instagram expects:
- Files with a .jpg extension that are actually PNG, WebP, or HEIC
- JPEG files in CMYK colorspace (e.g. exported from Lightroom/Photoshop)

The old code detected "is JPEG" via filename extension / stored MIME type.
The new code uses Pillow to inspect actual format and colorspace.
"""

import io
import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

# ---------------------------------------------------------------------------
# Pre-import patching: stub external service connections
# ---------------------------------------------------------------------------
os.environ.setdefault("FERNET_KEY", "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleXRlcz0=")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ROOT_USER", "minioadmin")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "minioadmin")

_mock_storage = MagicMock()
sys.modules.setdefault("app.core.storage", _mock_storage)


# ---------------------------------------------------------------------------
# Helpers to create minimal in-memory images
# ---------------------------------------------------------------------------

def _make_jpeg_bytes(mode: str = "RGB", size: tuple = (10, 10)) -> bytes:
    """Return raw JPEG bytes for an image with the given Pillow mode."""
    img = Image.new(mode, size, color=0)
    buf = io.BytesIO()
    # CMYK cannot be saved as JPEG directly without Pillow handling it
    save_img = img if mode != "CMYK" else img
    save_img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png_bytes(mode: str = "RGB", size: tuple = (10, 10)) -> bytes:
    """Return raw PNG bytes."""
    img = Image.new(mode, size, color=0)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_webp_bytes(size: tuple = (10, 10)) -> bytes:
    """Return raw WebP bytes."""
    img = Image.new("RGB", size, color=0)
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


def _make_cmyk_jpeg_bytes(size: tuple = (10, 10)) -> bytes:
    """Return raw JPEG bytes in CMYK colorspace (the primary bug trigger)."""
    img = Image.new("CMYK", size, color=(0, 0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Fixture: a minimal Media DB item
# ---------------------------------------------------------------------------

def _make_media_item(filename: str = "photo.jpg", mime_type: str = "image/jpeg",
                     file_path: str = "/app/uploads/photo.jpg") -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        user_id=42,
        filename=filename,
        mime_type=mime_type,
        file_path=file_path,
    )


# ---------------------------------------------------------------------------
# Import the function under test after patching
# ---------------------------------------------------------------------------

from app.api.v1.endpoints.instagram import _get_instagram_image_url  # noqa: E402


# ---------------------------------------------------------------------------
# Helper: build a fully-patched call context
# ---------------------------------------------------------------------------

def _call(
    raw_bytes: bytes,
    *,
    filename: str = "photo.jpg",
    mime_type: str = "image/jpeg",
    upload_ok: bool = True,
    presigned_url: str = "https://machine-systems.org/minio/temp/instagram_uuid.jpg",
    minio_get_bytes: bytes | None = None,
    local_file_missing: bool = False,
):
    """
    Call _get_instagram_image_url with fully mocked dependencies.

    ``raw_bytes`` is what Pillow will actually open (the real image content).
    """
    item = _make_media_item(filename=filename, mime_type=mime_type)
    mock_db = MagicMock()

    mock_media_service = MagicMock()
    mock_media_service.get_media.return_value = item
    mock_media_service.get_media_url.return_value = presigned_url
    mock_media_service._media_object_key.return_value = f"media/{filename}"

    mock_minio = MagicMock()
    mock_minio.get_object_bytes.return_value = minio_get_bytes or raw_bytes
    mock_minio.upload_data.return_value = upload_ok
    mock_minio.get_presigned_url.return_value = presigned_url
    mock_minio.delete_file.return_value = None

    # Decide how open() behaves
    if local_file_missing:
        open_side_effect = FileNotFoundError("not found")
    else:
        open_side_effect = None

    with patch("app.api.v1.endpoints.instagram.media_service", mock_media_service), \
         patch("app.api.v1.endpoints.instagram.minio_client", mock_minio), \
         patch("app.api.v1.endpoints.instagram._assert_url_is_public"), \
         patch("builtins.open",
               side_effect=open_side_effect if local_file_missing
               else lambda path, mode="r": io.BytesIO(raw_bytes)):
        url, temp_key = _get_instagram_image_url(
            media_id=item.id,
            user_id=item.user_id,
            db=mock_db,
        )

    return url, temp_key, mock_minio, mock_media_service


# ---------------------------------------------------------------------------
# Tests: RGB JPEG — no conversion needed
# ---------------------------------------------------------------------------

class TestRgbJpegNoConversion:
    """A genuine RGB JPEG must be sent as-is (no temp upload)."""

    def test_rgb_jpeg_returns_original_url(self):
        raw = _make_jpeg_bytes("RGB")
        url, temp_key, mock_minio, _ = _call(raw)

        assert temp_key is None
        mock_minio.upload_data.assert_not_called()

    def test_rgb_jpeg_url_is_presigned_original(self):
        raw = _make_jpeg_bytes("RGB")
        expected = "https://machine-systems.org/minio/media/photo.jpg?sig=abc"
        url, _, _, mock_media_service = _call(raw, presigned_url=expected)

        assert url == expected
        mock_media_service.get_media_url.assert_called_once()

    def test_greyscale_jpeg_returns_original_url(self):
        """Greyscale (mode='L') JPEG is accepted by Instagram without conversion."""
        raw = _make_jpeg_bytes("L")
        _, temp_key, mock_minio, _ = _call(raw)

        assert temp_key is None
        mock_minio.upload_data.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: CMYK JPEG — the primary bug scenario
# ---------------------------------------------------------------------------

class TestCmykJpegConversion:
    """CMYK JPEG (common from Lightroom/Photoshop exports) must be converted."""

    def test_cmyk_jpeg_triggers_conversion(self):
        raw = _make_cmyk_jpeg_bytes()
        _, temp_key, mock_minio, _ = _call(raw, filename="export.jpg", mime_type="image/jpeg")

        assert temp_key is not None
        mock_minio.upload_data.assert_called_once()
        # Verify it was uploaded as image/jpeg
        _, kwargs = mock_minio.upload_data.call_args
        assert kwargs.get("content_type") == "image/jpeg"

    def test_cmyk_jpeg_does_not_use_original_url(self):
        raw = _make_cmyk_jpeg_bytes()
        url, _, _, mock_media_service = _call(raw, filename="export.jpg", mime_type="image/jpeg")

        # get_media_url is for the original; it must NOT be called when we have a temp
        mock_media_service.get_media_url.assert_not_called()

    def test_cmyk_jpeg_returns_temp_presigned_url(self):
        raw = _make_cmyk_jpeg_bytes()
        expected_temp = "https://machine-systems.org/minio/temp/instagram_uuid.jpg"
        url, temp_key, mock_minio, _ = _call(raw, presigned_url=expected_temp)

        assert url == expected_temp
        assert temp_key is not None


# ---------------------------------------------------------------------------
# Tests: PNG / WebP with .jpg extension — caught by old code only if MIME differed
# ---------------------------------------------------------------------------

class TestNonJpegContentWithJpgExtension:
    """Files uploaded with a .jpg extension but containing PNG or WebP bytes."""

    def test_png_with_jpg_extension_triggers_conversion(self):
        raw = _make_png_bytes()
        # Old code would see .jpg extension → skip conversion → Instagram error
        _, temp_key, mock_minio, _ = _call(
            raw, filename="screenshot.jpg", mime_type="image/jpeg"
        )

        assert temp_key is not None
        mock_minio.upload_data.assert_called_once()

    def test_webp_with_jpg_extension_triggers_conversion(self):
        raw = _make_webp_bytes()
        _, temp_key, mock_minio, _ = _call(
            raw, filename="clip.jpg", mime_type="image/jpeg"
        )

        assert temp_key is not None
        mock_minio.upload_data.assert_called_once()

    def test_png_rgba_with_jpg_extension_converts_to_rgb_jpeg(self):
        """RGBA PNG (with alpha) must be flattened to RGB before JPEG encoding."""
        raw = _make_png_bytes(mode="RGBA")
        _, temp_key, mock_minio, _ = _call(
            raw, filename="transparent.jpg", mime_type="image/jpeg"
        )

        assert temp_key is not None
        # Verify the uploaded bytes are valid JPEG
        upload_bytes = mock_minio.upload_data.call_args[0][0]
        img = Image.open(io.BytesIO(upload_bytes))
        assert img.format == "JPEG"
        assert img.mode == "RGB"


# ---------------------------------------------------------------------------
# Tests: Local file missing — fall back to MinIO bytes
# ---------------------------------------------------------------------------

class TestLocalFileMissingFallback:
    """When the local file is gone, bytes should be fetched from MinIO."""

    def test_missing_local_file_fetches_from_minio(self):
        raw = _make_cmyk_jpeg_bytes()
        _, temp_key, mock_minio, _ = _call(raw, local_file_missing=True)

        mock_minio.get_object_bytes.assert_called_once()
        assert temp_key is not None  # conversion still happened

    def test_missing_local_rgb_jpeg_from_minio_no_conversion(self):
        raw = _make_jpeg_bytes("RGB")
        _, temp_key, mock_minio, _ = _call(raw, local_file_missing=True)

        mock_minio.get_object_bytes.assert_called_once()
        assert temp_key is None  # no conversion for valid RGB JPEG
        mock_minio.upload_data.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: Failure/fallback paths
# ---------------------------------------------------------------------------

class TestFallbackOnFailure:
    """If Pillow inspection or MinIO upload fails, fall back to the original URL."""

    def test_pillow_open_failure_falls_back_to_original(self):
        """Bytes that Pillow cannot identify as any image format fall through gracefully."""
        corrupt = b"this is plainly not an image format"  # Pillow raises UnidentifiedImageError
        item = _make_media_item()
        mock_db = MagicMock()

        mock_media_service = MagicMock()
        mock_media_service.get_media.return_value = item
        fallback_url = "https://machine-systems.org/minio/media/photo.jpg"
        mock_media_service.get_media_url.return_value = fallback_url

        mock_minio = MagicMock()

        with patch("app.api.v1.endpoints.instagram.media_service", mock_media_service), \
             patch("app.api.v1.endpoints.instagram.minio_client", mock_minio), \
             patch("app.api.v1.endpoints.instagram._assert_url_is_public"), \
             patch("builtins.open", lambda path, mode="r": io.BytesIO(corrupt)):
            url, temp_key = _get_instagram_image_url(1, 42, mock_db)

        assert temp_key is None
        assert url == fallback_url
        mock_minio.upload_data.assert_not_called()

    def test_minio_upload_failure_falls_back_to_original(self):
        """If MinIO upload fails after conversion, fall back to the original URL."""
        raw = _make_cmyk_jpeg_bytes()
        fallback_url = "https://machine-systems.org/minio/media/photo.jpg"
        url, temp_key, mock_minio, _ = _call(
            raw, upload_ok=False, presigned_url=fallback_url
        )

        assert temp_key is None
        assert url == fallback_url
        mock_minio.upload_data.assert_called_once()
        mock_minio.delete_file.assert_not_called()  # upload failed; no key to clean up

    def test_presigned_url_none_cleans_up_and_falls_back(self):
        """If get_presigned_url returns None after upload, temp object is deleted."""
        raw = _make_cmyk_jpeg_bytes()
        item = _make_media_item()
        mock_db = MagicMock()

        fallback_url = "https://machine-systems.org/minio/media/photo.jpg"
        mock_media_service = MagicMock()
        mock_media_service.get_media.return_value = item
        mock_media_service.get_media_url.return_value = fallback_url
        mock_media_service._media_object_key.return_value = "media/photo.jpg"

        mock_minio = MagicMock()
        mock_minio.upload_data.return_value = True
        mock_minio.get_presigned_url.return_value = None  # URL generation fails
        mock_minio.delete_file.return_value = None

        with patch("app.api.v1.endpoints.instagram.media_service", mock_media_service), \
             patch("app.api.v1.endpoints.instagram.minio_client", mock_minio), \
             patch("app.api.v1.endpoints.instagram._assert_url_is_public"), \
             patch("builtins.open", lambda path, mode="r": io.BytesIO(raw)):
            url, temp_key = _get_instagram_image_url(1, 42, mock_db)

        assert temp_key is None
        assert url == fallback_url
        mock_minio.delete_file.assert_called_once()  # cleaned up the orphaned temp object
