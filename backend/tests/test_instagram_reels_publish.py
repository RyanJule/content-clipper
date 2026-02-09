"""
Tests for Instagram Reels (video) publishing.

Covers:
- InstagramGraphAPI.create_video_container
- InstagramGraphAPI.check_container_status
- _publish_to_instagram (video/reel path with status polling)
- publish_post end-to-end (reel to Instagram)
- Error scenarios (processing timeout, processing error, bad token, API failures)
"""

import json
import os
import sys
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Pre-import patching: prevent modules that connect to external services
# (MinIO, Redis, database) from loading during test collection.
# ---------------------------------------------------------------------------
os.environ.setdefault("FERNET_KEY", "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleXRlcz0=")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ROOT_USER", "minioadmin")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "minioadmin")

# Stub out the storage module so MinIO doesn't try to connect
_mock_storage = MagicMock()
sys.modules.setdefault("app.core.storage", _mock_storage)

import httpx
import pytest
import pytest_asyncio

from app.services.instagram_graph_service import (
    InstagramGraphAPI,
    InstagramGraphAPIError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def ig_api():
    """Create an InstagramGraphAPI instance with a fake token."""
    api = InstagramGraphAPI(access_token="fake-access-token")
    yield api
    await api.close()


@pytest.fixture
def mock_clip_video():
    """A clip-like object representing a video (reel)."""
    clip = SimpleNamespace(
        id=2,
        media_url="https://storage.example.com/videos/clip.mp4",
        media_type="video",
        file_path="videos/clip.mp4",
    )
    return clip


@pytest.fixture
def mock_clip_reel():
    """A clip-like object with explicit 'reel' media_type."""
    clip = SimpleNamespace(
        id=5,
        media_url="https://storage.example.com/videos/reel.mp4",
        media_type="reel",
        file_path="videos/reel.mp4",
    )
    return clip


@pytest.fixture
def mock_account():
    """An Account-like object with encrypted token and meta_info."""
    account = SimpleNamespace(
        id=1,
        user_id=1,
        platform="instagram",
        account_username="testuser",
        access_token_enc="encrypted-token-value",
        is_active=True,
        meta_info={
            "instagram_business_account_id": "17841400123456789",
            "facebook_page_id": "100200300",
        },
    )
    return account


@pytest.fixture
def mock_post_video():
    """A SocialPost-like object for video publishing."""
    post = SimpleNamespace(
        id=30,
        user_id=1,
        clip_id=2,
        platform=SimpleNamespace(value="instagram"),
        caption="Check out this reel!",
        hashtags=json.dumps(["#reels", "#video", "#trending"]),
        status="publishing",
    )
    return post


# ---------------------------------------------------------------------------
# InstagramGraphAPI unit tests – video/reel container
# ---------------------------------------------------------------------------

class TestCreateVideoContainer:
    """Tests for InstagramGraphAPI.create_video_container"""

    @pytest.mark.asyncio
    async def test_create_video_container_basic(self, ig_api):
        """Creating a video container returns a container ID."""
        mock_response = httpx.Response(
            200,
            json={"id": "video_container_123"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig_id/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        container_id = await ig_api.create_video_container(
            ig_account_id="17841400123456789",
            video_url="https://storage.example.com/video.mp4",
            caption="Test video",
        )

        assert container_id == "video_container_123"
        ig_api.client.post.assert_called_once()
        call_kwargs = ig_api.client.post.call_args
        assert "17841400123456789/media" in call_kwargs.args[0]

    @pytest.mark.asyncio
    async def test_create_video_container_default_media_type_reels(self, ig_api):
        """Default media_type is REELS."""
        mock_response = httpx.Response(
            200,
            json={"id": "reel_c"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_video_container(
            ig_account_id="ig_id",
            video_url="https://example.com/video.mp4",
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["media_type"] == "REELS"

    @pytest.mark.asyncio
    async def test_create_video_container_explicit_video_type(self, ig_api):
        """Explicit VIDEO media_type is sent correctly."""
        mock_response = httpx.Response(
            200,
            json={"id": "vid_c"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_video_container(
            ig_account_id="ig_id",
            video_url="https://example.com/video.mp4",
            media_type="VIDEO",
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["media_type"] == "VIDEO"

    @pytest.mark.asyncio
    async def test_create_video_container_with_caption(self, ig_api):
        """Caption is included in the video container request."""
        mock_response = httpx.Response(
            200,
            json={"id": "vid_cap"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_video_container(
            ig_account_id="ig_id",
            video_url="https://example.com/video.mp4",
            caption="My awesome reel",
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["caption"] == "My awesome reel"

    @pytest.mark.asyncio
    async def test_create_video_container_no_caption(self, ig_api):
        """Video container without caption omits it from request."""
        mock_response = httpx.Response(
            200,
            json={"id": "vid_nc"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_video_container(
            ig_account_id="ig_id",
            video_url="https://example.com/video.mp4",
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert "caption" not in data_arg

    @pytest.mark.asyncio
    async def test_create_video_container_with_location(self, ig_api):
        """Location ID is included in the video container request."""
        mock_response = httpx.Response(
            200,
            json={"id": "vid_loc"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_video_container(
            ig_account_id="ig_id",
            video_url="https://example.com/video.mp4",
            location_id="loc_123",
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["location_id"] == "loc_123"

    @pytest.mark.asyncio
    async def test_create_video_container_with_thumb_offset(self, ig_api):
        """Thumbnail offset is included in the video container request."""
        mock_response = httpx.Response(
            200,
            json={"id": "vid_thumb"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_video_container(
            ig_account_id="ig_id",
            video_url="https://example.com/video.mp4",
            thumb_offset=5000,
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["thumb_offset"] == 5000

    @pytest.mark.asyncio
    async def test_create_video_container_api_error(self, ig_api):
        """API error during video container creation raises InstagramGraphAPIError."""
        error_response = httpx.Response(
            400,
            json={"error": {"message": "Invalid video URL", "type": "OAuthException", "code": 100}},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Bad Request", request=error_response.request, response=error_response
        ))

        with pytest.raises(InstagramGraphAPIError, match="Invalid video URL"):
            await ig_api.create_video_container(
                ig_account_id="ig_id",
                video_url="https://example.com/bad.mp4",
            )


class TestCheckContainerStatus:
    """Tests for InstagramGraphAPI.check_container_status"""

    @pytest.mark.asyncio
    async def test_check_container_status_finished(self, ig_api):
        """Checking status of a finished container returns FINISHED."""
        mock_response = httpx.Response(
            200,
            json={"id": "container_1", "status_code": "FINISHED", "status": "ready"},
            request=httpx.Request("GET", "https://graph.facebook.com/v18.0/container_1"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.get = AsyncMock(return_value=mock_response)

        result = await ig_api.check_container_status("container_1")

        assert result["status_code"] == "FINISHED"
        assert result["id"] == "container_1"

    @pytest.mark.asyncio
    async def test_check_container_status_in_progress(self, ig_api):
        """Checking status of a processing container returns IN_PROGRESS."""
        mock_response = httpx.Response(
            200,
            json={"id": "container_2", "status_code": "IN_PROGRESS", "status": "processing"},
            request=httpx.Request("GET", "https://graph.facebook.com/v18.0/container_2"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.get = AsyncMock(return_value=mock_response)

        result = await ig_api.check_container_status("container_2")

        assert result["status_code"] == "IN_PROGRESS"

    @pytest.mark.asyncio
    async def test_check_container_status_error(self, ig_api):
        """Checking status of a failed container returns ERROR."""
        mock_response = httpx.Response(
            200,
            json={"id": "container_3", "status_code": "ERROR", "status": "Video format not supported"},
            request=httpx.Request("GET", "https://graph.facebook.com/v18.0/container_3"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.get = AsyncMock(return_value=mock_response)

        result = await ig_api.check_container_status("container_3")

        assert result["status_code"] == "ERROR"
        assert "not supported" in result["status"]

    @pytest.mark.asyncio
    async def test_check_container_status_requests_correct_fields(self, ig_api):
        """Status check requests the correct fields."""
        mock_response = httpx.Response(
            200,
            json={"id": "c", "status_code": "FINISHED"},
            request=httpx.Request("GET", "https://graph.facebook.com/v18.0/c"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.get = AsyncMock(return_value=mock_response)

        await ig_api.check_container_status("container_id_1")

        call_kwargs = ig_api.client.get.call_args
        params = call_kwargs.kwargs.get("params", {})
        assert "status_code" in params.get("fields", "")
        assert "status" in params.get("fields", "")


# ---------------------------------------------------------------------------
# _publish_to_instagram unit tests (video/reel path)
# ---------------------------------------------------------------------------

class TestPublishToInstagramReel:
    """Tests for the _publish_to_instagram helper with video/reel posts."""

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_reel_publish_success(
        self, mock_sleep, mock_decrypt, mock_post_video, mock_clip_video, mock_account
    ):
        """Successfully publishing a reel returns platform_post_id and URL."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance

            mock_api_instance.create_video_container = AsyncMock(
                return_value="video_container_1"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "FINISHED"}
            )
            mock_api_instance.publish_container = AsyncMock(return_value="media_reel_1")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "id": "media_reel_1",
                "permalink": "https://www.instagram.com/reel/REEL123/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(
                mock_post_video, mock_clip_video, mock_account
            )

            assert result["platform_post_id"] == "media_reel_1"
            assert result["platform_url"] == "https://www.instagram.com/reel/REEL123/"

            # Verify video container was created (not image)
            mock_api_instance.create_video_container.assert_called_once()
            mock_api_instance.create_image_container.assert_not_called()

            # Verify container was published with REELS media type
            create_kwargs = mock_api_instance.create_video_container.call_args
            assert create_kwargs.kwargs["media_type"] == "REELS"

            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_reel_publish_with_reel_media_type(
        self, mock_sleep, mock_decrypt, mock_post_video, mock_clip_reel, mock_account
    ):
        """media_type='reel' also uses video container path."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_video_container = AsyncMock(
                return_value="reel_container"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "FINISHED"}
            )
            mock_api_instance.publish_container = AsyncMock(return_value="media_reel")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://www.instagram.com/reel/REEL/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(
                mock_post_video, mock_clip_reel, mock_account
            )

            assert result["platform_post_id"] == "media_reel"
            mock_api_instance.create_video_container.assert_called_once()
            mock_api_instance.create_image_container.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_reel_publish_caption_with_hashtags(
        self, mock_sleep, mock_decrypt, mock_post_video, mock_clip_video, mock_account
    ):
        """Video caption includes appended hashtags."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_video_container = AsyncMock(
                return_value="vc"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "FINISHED"}
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m1")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://instagram.com/reel/X/",
            })
            mock_api_instance.close = AsyncMock()

            await _publish_to_instagram(
                mock_post_video, mock_clip_video, mock_account
            )

            call_kwargs = mock_api_instance.create_video_container.call_args
            caption_sent = call_kwargs.kwargs.get("caption", "")
            assert "#reels" in caption_sent
            assert "#video" in caption_sent
            assert "Check out this reel!" in caption_sent

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_reel_publish_waits_for_processing(
        self, mock_sleep, mock_decrypt, mock_post_video, mock_clip_video, mock_account
    ):
        """Publishing waits while video container is IN_PROGRESS."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_video_container = AsyncMock(
                return_value="vc_slow"
            )
            # Processing takes 3 checks before finishing
            mock_api_instance.check_container_status = AsyncMock(
                side_effect=[
                    {"status_code": "IN_PROGRESS"},
                    {"status_code": "IN_PROGRESS"},
                    {"status_code": "FINISHED"},
                ]
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m_slow")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://instagram.com/reel/SLOW/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(
                mock_post_video, mock_clip_video, mock_account
            )

            assert result["platform_post_id"] == "m_slow"
            # Status checked 3 times
            assert mock_api_instance.check_container_status.call_count == 3
            # Sleep called 2 times (before 2nd and 3rd check)
            assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_reel_publish_processing_error(
        self, mock_sleep, mock_decrypt, mock_post_video, mock_clip_video, mock_account
    ):
        """Video processing ERROR raises InstagramGraphAPIError via ValueError."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_video_container = AsyncMock(
                return_value="vc_err"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "ERROR", "status": "Codec not supported"}
            )
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="Video processing failed"):
                await _publish_to_instagram(
                    mock_post_video, mock_clip_video, mock_account
                )

            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_reel_publish_processing_timeout(
        self, mock_sleep, mock_decrypt, mock_post_video, mock_clip_video, mock_account
    ):
        """Video processing timeout raises InstagramGraphAPIError via ValueError."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_video_container = AsyncMock(
                return_value="vc_timeout"
            )
            # Always return IN_PROGRESS – never FINISHED
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "IN_PROGRESS"}
            )
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="Video processing timeout"):
                await _publish_to_instagram(
                    mock_post_video, mock_clip_video, mock_account
                )

            # check_container_status called 30 times (max_attempts)
            assert mock_api_instance.check_container_status.call_count == 30
            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_reel_publish_container_creation_api_error(
        self, mock_decrypt, mock_post_video, mock_clip_video, mock_account
    ):
        """API error during video container creation propagates as ValueError."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_video_container = AsyncMock(
                side_effect=InstagramGraphAPIError("Video too large")
            )
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="Instagram API error.*Video too large"):
                await _publish_to_instagram(
                    mock_post_video, mock_clip_video, mock_account
                )

            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_reel_publish_publish_api_error(
        self, mock_sleep, mock_decrypt, mock_post_video, mock_clip_video, mock_account
    ):
        """API error during publish step propagates as ValueError."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_video_container = AsyncMock(
                return_value="vc_pub_err"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "FINISHED"}
            )
            mock_api_instance.publish_container = AsyncMock(
                side_effect=InstagramGraphAPIError("Container expired")
            )
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="Instagram API error.*Container expired"):
                await _publish_to_instagram(
                    mock_post_video, mock_clip_video, mock_account
                )

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value=None)
    async def test_reel_publish_invalid_token(
        self, mock_decrypt, mock_post_video, mock_clip_video, mock_account
    ):
        """Invalid (None) access token raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        with pytest.raises(ValueError, match="Invalid access token"):
            await _publish_to_instagram(
                mock_post_video, mock_clip_video, mock_account
            )

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_reel_publish_missing_media_url(
        self, mock_decrypt, mock_post_video, mock_account
    ):
        """Missing media_url on clip raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        clip = SimpleNamespace(id=10, media_type="video")

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="does not have a media URL"):
                await _publish_to_instagram(mock_post_video, clip, mock_account)

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_reel_publish_no_hashtags(
        self, mock_sleep, mock_decrypt, mock_clip_video, mock_account
    ):
        """Post without hashtags publishes caption as-is."""
        from app.services.social_service import _publish_to_instagram

        post = SimpleNamespace(
            id=31,
            user_id=1,
            clip_id=2,
            platform=SimpleNamespace(value="instagram"),
            caption="No tags reel",
            hashtags=None,
            status="publishing",
        )

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_video_container = AsyncMock(return_value="vc1")
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "FINISHED"}
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m1")
            mock_api_instance.get_media_details = AsyncMock(
                return_value={"permalink": "https://instagram.com/reel/X/"}
            )
            mock_api_instance.close = AsyncMock()

            await _publish_to_instagram(post, mock_clip_video, mock_account)

            call_kwargs = mock_api_instance.create_video_container.call_args
            caption_sent = call_kwargs.kwargs.get("caption", "")
            assert caption_sent == "No tags reel"


# ---------------------------------------------------------------------------
# publish_post end-to-end tests (reel to Instagram)
# ---------------------------------------------------------------------------

class TestPublishPostReelEndToEnd:
    """End-to-end tests for publish_post with Instagram reel/video posts."""

    def _make_db_post(self, status="draft"):
        """Create a mock SocialPost DB object for reel."""
        post = MagicMock()
        post.id = 30
        post.user_id = 1
        post.clip_id = 2
        post.platform = MagicMock()
        post.platform.value = "instagram"
        post.platform.__eq__ = lambda self, other: (
            getattr(other, 'value', other) == "instagram" or other == self
        )
        post.caption = "E2E reel test"
        post.hashtags = json.dumps(["#test"])
        post.status = status
        post.published_at = None
        post.platform_post_id = None
        post.platform_url = None
        post.error_message = None
        return post

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_publish_post_reel_success(self, mock_sleep, mock_decrypt):
        """Full publish_post flow for an Instagram reel succeeds."""
        from app.services.social_service import publish_post, PostStatus, SocialPlatform

        db_post = self._make_db_post()
        db_post.platform = SocialPlatform.INSTAGRAM

        mock_clip = SimpleNamespace(
            id=2,
            media_url="https://storage.example.com/reel.mp4",
            media_type="video",
        )
        mock_account = MagicMock()
        mock_account.access_token_enc = "enc-token"
        mock_account.meta_info = {"instagram_business_account_id": "ig_123"}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = db_post

        with patch("app.services.social_service.get_post", return_value=db_post), \
             patch("app.services.social_service.get_clip", return_value=mock_clip), \
             patch("app.services.social_service.InstagramGraphAPI") as MockAPI:

            mock_db.query.return_value.filter.return_value.first.return_value = mock_account

            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_video_container = AsyncMock(
                return_value="vc_e2e"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "FINISHED"}
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m_reel_e2e")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://www.instagram.com/reel/REEL_E2E/",
            })
            mock_api_instance.close = AsyncMock()

            result = await publish_post(mock_db, post_id=30)

            assert result["success"] is True
            assert result["post_id"] == 30
            assert "REEL_E2E" in result.get("platform_url", "")

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_publish_post_reel_processing_error_marks_failed(
        self, mock_sleep, mock_decrypt
    ):
        """When video processing fails, post status is set to FAILED."""
        from app.services.social_service import publish_post, PostStatus, SocialPlatform

        db_post = self._make_db_post()
        db_post.platform = SocialPlatform.INSTAGRAM

        mock_clip = SimpleNamespace(
            id=2,
            media_url="https://storage.example.com/reel.mp4",
            media_type="video",
        )
        mock_account = MagicMock()
        mock_account.access_token_enc = "enc-token"
        mock_account.meta_info = {"instagram_business_account_id": "ig_123"}

        mock_db = MagicMock()

        with patch("app.services.social_service.get_post", return_value=db_post), \
             patch("app.services.social_service.get_clip", return_value=mock_clip), \
             patch("app.services.social_service.InstagramGraphAPI") as MockAPI:

            mock_db.query.return_value.filter.return_value.first.return_value = mock_account

            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_video_container = AsyncMock(
                return_value="vc_fail"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "ERROR", "status": "Unsupported format"}
            )
            mock_api_instance.close = AsyncMock()

            result = await publish_post(mock_db, post_id=30)

            assert result["success"] is False
            assert "error" in result
            assert db_post.status == PostStatus.FAILED
            assert db_post.error_message is not None
