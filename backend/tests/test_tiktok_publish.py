"""
Tests for TikTok video.publish (direct post) integration.

Covers:
- publish_video_by_url: uses /post/publish/video/init/ with DIRECT_POST mode
- init_video_upload: uses /post/publish/video/init/ with post_info for file uploads
- upload_video_bytes: end-to-end bytes upload triggering direct publish init
- get_publish_status: status polling endpoint
- Error handling: auth errors, missing publish_id, API errors
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("FERNET_KEY", "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleXRlcz0=")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ROOT_USER", "minioadmin")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "minioadmin")

# Stub out modules that connect to external services or have heavy dependencies
for _mod in (
    "app.core.storage",
    "app.services.media_service",
    "app.services.clip_service",
    "app.services.social_service",
    "app.services.user_service",
    "app.services.oauth_service",
    "aiofiles",
    "celery",
    "redis",
    "minio",
    "openai",
    "ffmpeg",
):
    sys.modules.setdefault(_mod, MagicMock())

import httpx
import pytest
import pytest_asyncio

from app.services.tiktok_service import (
    TikTokAPIError,
    TikTokAuthError,
    TikTokService,
    create_tiktok_service,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def tt():
    """TikTokService with a fake access token."""
    service = TikTokService(access_token="fake-access-token")
    yield service
    await service.close()


def _ok_response(json_body: dict, url: str = "https://open.tiktokapis.com/v2/post/publish/video/init/") -> httpx.Response:
    """Helper to build a successful TikTok API httpx.Response."""
    return httpx.Response(
        200,
        json=json_body,
        request=httpx.Request("POST", url),
    )


def _error_response(code: str, message: str, http_status: int = 200) -> httpx.Response:
    """Helper to build a TikTok error response (errors are in the body, not HTTP status)."""
    return httpx.Response(
        http_status,
        json={"error": {"code": code, "message": message, "log_id": "test-log"}},
        request=httpx.Request("POST", "https://open.tiktokapis.com/v2/test/"),
    )


# ---------------------------------------------------------------------------
# publish_video_by_url
# ---------------------------------------------------------------------------

class TestPublishVideoByUrl:
    """Tests for TikTokService.publish_video_by_url (video.publish direct post)."""

    @pytest.mark.asyncio
    async def test_uses_direct_post_endpoint(self, tt):
        """publish_video_by_url must call /post/publish/video/init/, not the inbox endpoint."""
        mock_response = _ok_response({"data": {"publish_id": "pub_abc123"}, "error": {"code": "ok"}})
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        result = await tt.publish_video_by_url(video_url="https://example.com/video.mp4")

        assert result["publish_id"] == "pub_abc123"
        tt.client.post.assert_called_once()
        called_url = tt.client.post.call_args.args[0]
        assert "post/publish/video/init/" in called_url
        assert "inbox" not in called_url

    @pytest.mark.asyncio
    async def test_body_contains_post_info(self, tt):
        """publish_video_by_url must include post_info with all post metadata."""
        mock_response = _ok_response({"data": {"publish_id": "pub_xyz"}, "error": {"code": "ok"}})
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        await tt.publish_video_by_url(
            video_url="https://example.com/video.mp4",
            title="My TikTok",
            privacy_level="PUBLIC_TO_EVERYONE",
            disable_duet=True,
            disable_comment=True,
            disable_stitch=False,
            video_cover_timestamp_ms=1000,
        )

        call_kwargs = tt.client.post.call_args.kwargs
        body = call_kwargs["json"]
        assert "post_info" in body
        assert body["post_info"]["title"] == "My TikTok"
        assert body["post_info"]["privacy_level"] == "PUBLIC_TO_EVERYONE"
        assert body["post_info"]["disable_duet"] is True
        assert body["post_info"]["disable_comment"] is True
        assert body["post_info"]["disable_stitch"] is False
        assert body["post_info"]["video_cover_timestamp_ms"] == 1000

    @pytest.mark.asyncio
    async def test_body_contains_direct_post_mode(self, tt):
        """publish_video_by_url must set post_mode=DIRECT_POST and media_type=VIDEO."""
        mock_response = _ok_response({"data": {"publish_id": "pub_direct"}, "error": {"code": "ok"}})
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        await tt.publish_video_by_url(video_url="https://example.com/video.mp4")

        body = tt.client.post.call_args.kwargs["json"]
        assert body["post_mode"] == "DIRECT_POST"
        assert body["media_type"] == "VIDEO"

    @pytest.mark.asyncio
    async def test_body_contains_pull_from_url_source(self, tt):
        """publish_video_by_url must include source_info with PULL_FROM_URL and the video URL."""
        mock_response = _ok_response({"data": {"publish_id": "pub_url"}, "error": {"code": "ok"}})
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        video_url = "https://cdn.example.com/clip.mp4"
        await tt.publish_video_by_url(video_url=video_url)

        body = tt.client.post.call_args.kwargs["json"]
        assert body["source_info"]["source"] == "PULL_FROM_URL"
        assert body["source_info"]["video_url"] == video_url

    @pytest.mark.asyncio
    async def test_title_truncated_to_2200_chars(self, tt):
        """Titles longer than 2200 characters are silently truncated."""
        mock_response = _ok_response({"data": {"publish_id": "pub_trunc"}, "error": {"code": "ok"}})
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        long_title = "x" * 3000
        await tt.publish_video_by_url(video_url="https://example.com/v.mp4", title=long_title)

        body = tt.client.post.call_args.kwargs["json"]
        assert len(body["post_info"]["title"]) == 2200

    @pytest.mark.asyncio
    async def test_missing_publish_id_raises(self, tt):
        """publish_video_by_url raises TikTokAPIError when publish_id is absent."""
        mock_response = _ok_response({"data": {}, "error": {"code": "ok"}})
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(TikTokAPIError, match="No publish_id"):
            await tt.publish_video_by_url(video_url="https://example.com/v.mp4")

    @pytest.mark.asyncio
    async def test_auth_error_raises_tiktok_auth_error(self, tt):
        """Auth error codes in the response body raise TikTokAuthError."""
        mock_response = _error_response("access_token_invalid", "Invalid token")
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(TikTokAuthError):
            await tt.publish_video_by_url(video_url="https://example.com/v.mp4")

    @pytest.mark.asyncio
    async def test_api_error_raises_tiktok_api_error(self, tt):
        """Non-auth TikTok error codes raise TikTokAPIError."""
        mock_response = _error_response("spam_risk_too_many_posts", "Too many posts")
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(TikTokAPIError):
            await tt.publish_video_by_url(video_url="https://example.com/v.mp4")


# ---------------------------------------------------------------------------
# init_video_upload
# ---------------------------------------------------------------------------

class TestInitVideoUpload:
    """Tests for TikTokService.init_video_upload (direct post, file-based)."""

    @pytest.mark.asyncio
    async def test_uses_direct_post_endpoint(self, tt):
        """init_video_upload must call /post/publish/video/init/, not the inbox endpoint."""
        mock_response = _ok_response({
            "data": {"publish_id": "pub_file", "upload_url": "https://upload.tiktok.com/xyz"},
            "error": {"code": "ok"},
        })
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        result = await tt.init_video_upload(video_size=1024 * 1024)

        assert result["publish_id"] == "pub_file"
        assert result["upload_url"] == "https://upload.tiktok.com/xyz"
        called_url = tt.client.post.call_args.args[0]
        assert "post/publish/video/init/" in called_url
        assert "inbox" not in called_url

    @pytest.mark.asyncio
    async def test_body_contains_post_info(self, tt):
        """init_video_upload must include post_info with post metadata."""
        mock_response = _ok_response({
            "data": {"publish_id": "pub_pi", "upload_url": "https://upload.tiktok.com/abc"},
            "error": {"code": "ok"},
        })
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        await tt.init_video_upload(
            video_size=1024 * 1024,
            title="My upload",
            privacy_level="SELF_ONLY",
            disable_duet=False,
            disable_stitch=True,
        )

        body = tt.client.post.call_args.kwargs["json"]
        assert "post_info" in body
        assert body["post_info"]["title"] == "My upload"
        assert body["post_info"]["privacy_level"] == "SELF_ONLY"
        assert body["post_info"]["disable_stitch"] is True

    @pytest.mark.asyncio
    async def test_body_contains_direct_post_mode(self, tt):
        """init_video_upload must set post_mode=DIRECT_POST and media_type=VIDEO."""
        mock_response = _ok_response({
            "data": {"publish_id": "pub_dm", "upload_url": "https://upload.tiktok.com/dm"},
            "error": {"code": "ok"},
        })
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        await tt.init_video_upload(video_size=1024 * 1024)

        body = tt.client.post.call_args.kwargs["json"]
        assert body["post_mode"] == "DIRECT_POST"
        assert body["media_type"] == "VIDEO"

    @pytest.mark.asyncio
    async def test_small_file_single_chunk(self, tt):
        """Files <= 64MB are sent as a single chunk."""
        mock_response = _ok_response({
            "data": {"publish_id": "pub_small", "upload_url": "https://upload.tiktok.com/s"},
            "error": {"code": "ok"},
        })
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        small_size = 10 * 1024 * 1024  # 10 MB
        await tt.init_video_upload(video_size=small_size)

        body = tt.client.post.call_args.kwargs["json"]
        assert body["source_info"]["source"] == "FILE_UPLOAD"
        assert body["source_info"]["total_chunk_count"] == 1
        assert body["source_info"]["chunk_size"] == small_size

    @pytest.mark.asyncio
    async def test_large_file_chunked(self, tt):
        """Files > 64MB are split into 10MB chunks."""
        mock_response = _ok_response({
            "data": {"publish_id": "pub_large", "upload_url": "https://upload.tiktok.com/l"},
            "error": {"code": "ok"},
        })
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        large_size = 200 * 1024 * 1024  # 200 MB
        await tt.init_video_upload(video_size=large_size)

        body = tt.client.post.call_args.kwargs["json"]
        assert body["source_info"]["total_chunk_count"] > 1
        assert body["source_info"]["chunk_size"] == tt.CHUNK_SIZE

    @pytest.mark.asyncio
    async def test_missing_upload_url_raises(self, tt):
        """init_video_upload raises when upload_url is absent from the response."""
        mock_response = _ok_response({
            "data": {"publish_id": "pub_no_url"},
            "error": {"code": "ok"},
        })
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(TikTokAPIError, match="missing publish_id or upload_url"):
            await tt.init_video_upload(video_size=1024)


# ---------------------------------------------------------------------------
# upload_video_bytes (end-to-end: init + PUT upload)
# ---------------------------------------------------------------------------

class TestUploadVideoBytes:
    """Tests for TikTokService.upload_video_bytes triggering direct publish init."""

    @pytest.mark.asyncio
    async def test_small_video_single_put(self, tt):
        """Uploading a small video results in one PUT to the upload URL."""
        init_response = _ok_response({
            "data": {
                "publish_id": "pub_bytes",
                "upload_url": "https://upload.tiktok.com/bytes_upload",
            },
            "error": {"code": "ok"},
        })
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=init_response)

        put_response = httpx.Response(
            200,
            text="",
            request=httpx.Request("PUT", "https://upload.tiktok.com/bytes_upload"),
        )

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_instance.put = AsyncMock(return_value=put_response)
            mock_client_cls.return_value = mock_client_instance

            video_data = b"\x00" * (10 * 1024 * 1024)  # 10 MB
            result = await tt.upload_video_bytes(
                video_data=video_data,
                title="Test video",
                privacy_level="SELF_ONLY",
            )

        assert result["publish_id"] == "pub_bytes"
        # Confirm init was called on the direct-post endpoint
        called_url = tt.client.post.call_args.args[0]
        assert "post/publish/video/init/" in called_url
        assert "inbox" not in called_url

    @pytest.mark.asyncio
    async def test_video_too_large_raises(self, tt):
        """Videos exceeding 4GB raise TikTokAPIError before any API call."""
        tt.client = AsyncMock()

        oversized = b"\x00" * 1  # dummy; we patch len() effectively via size check
        # Patch to make it appear as 5GB
        with patch.object(TikTokService, "MAX_VIDEO_SIZE", 0):
            with pytest.raises(TikTokAPIError, match="exceeds maximum size"):
                await tt.upload_video_bytes(video_data=oversized)

        tt.client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_progress_callback_invoked(self, tt):
        """on_progress callback is called after a successful small-file upload."""
        init_response = _ok_response({
            "data": {
                "publish_id": "pub_prog",
                "upload_url": "https://upload.tiktok.com/prog",
            },
            "error": {"code": "ok"},
        })
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=init_response)

        put_response = httpx.Response(
            200,
            text="",
            request=httpx.Request("PUT", "https://upload.tiktok.com/prog"),
        )

        progress_calls = []

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_instance.put = AsyncMock(return_value=put_response)
            mock_client_cls.return_value = mock_client_instance

            video_data = b"\x00" * (5 * 1024 * 1024)  # 5 MB
            await tt.upload_video_bytes(
                video_data=video_data,
                on_progress=lambda uploaded, total: progress_calls.append((uploaded, total)),
            )

        assert len(progress_calls) == 1
        uploaded, total = progress_calls[0]
        assert uploaded == total == len(video_data)


# ---------------------------------------------------------------------------
# get_publish_status
# ---------------------------------------------------------------------------

class TestGetPublishStatus:
    """Tests for TikTokService.get_publish_status."""

    @pytest.mark.asyncio
    async def test_returns_status_data(self, tt):
        """get_publish_status returns the data block from the TikTok response."""
        mock_response = httpx.Response(
            200,
            json={
                "data": {"status": "PUBLISH_COMPLETE", "publicaly_available_post_id": ["vid_001"]},
                "error": {"code": "ok"},
            },
            request=httpx.Request("POST", "https://open.tiktokapis.com/v2/post/publish/status/fetch/"),
        )
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        status = await tt.get_publish_status("pub_abc123")

        assert status["status"] == "PUBLISH_COMPLETE"
        called_url = tt.client.post.call_args.args[0]
        assert "post/publish/status/fetch/" in called_url

    @pytest.mark.asyncio
    async def test_processing_status_returned(self, tt):
        """Intermediate statuses like PROCESSING_UPLOAD are returned as-is."""
        mock_response = httpx.Response(
            200,
            json={"data": {"status": "PROCESSING_UPLOAD"}, "error": {"code": "ok"}},
            request=httpx.Request("POST", "https://open.tiktokapis.com/v2/post/publish/status/fetch/"),
        )
        tt.client = AsyncMock()
        tt.client.post = AsyncMock(return_value=mock_response)

        status = await tt.get_publish_status("pub_processing")

        assert status["status"] == "PROCESSING_UPLOAD"


# ---------------------------------------------------------------------------
# create_tiktok_service factory
# ---------------------------------------------------------------------------

def test_create_tiktok_service_returns_instance():
    """create_tiktok_service produces a TikTokService with the given token."""
    service = create_tiktok_service("test-token-abc")
    assert isinstance(service, TikTokService)
    assert service.access_token == "test-token-abc"
