"""
Tests for Instagram Stories publishing.

Covers:
- InstagramGraphAPI.create_story_container (image and video)
- _publish_to_instagram (story path)
- publish_post end-to-end (story to Instagram)
- Error scenarios (bad token, API failures, video story processing)
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
def mock_clip_story_image():
    """A clip-like object representing an image story."""
    clip = SimpleNamespace(
        id=10,
        media_url="https://storage.example.com/images/story.jpg",
        media_type="story",
        file_path="images/story.jpg",
        story_media_type="IMAGE",
    )
    return clip


@pytest.fixture
def mock_clip_story_video():
    """A clip-like object representing a video story."""
    clip = SimpleNamespace(
        id=11,
        media_url="https://storage.example.com/videos/story.mp4",
        media_type="story",
        file_path="videos/story.mp4",
        story_media_type="VIDEO",
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
def mock_post_story():
    """A SocialPost-like object for story publishing."""
    post = SimpleNamespace(
        id=40,
        user_id=1,
        clip_id=10,
        platform=SimpleNamespace(value="instagram"),
        caption="Story time!",
        hashtags=None,
        status="publishing",
    )
    return post


# ---------------------------------------------------------------------------
# InstagramGraphAPI unit tests – story container
# ---------------------------------------------------------------------------

class TestCreateStoryContainer:
    """Tests for InstagramGraphAPI.create_story_container"""

    @pytest.mark.asyncio
    async def test_create_story_container_image(self, ig_api):
        """Creating an image story container returns a container ID."""
        mock_response = httpx.Response(
            200,
            json={"id": "story_container_img"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig_id/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        container_id = await ig_api.create_story_container(
            ig_account_id="17841400123456789",
            media_url="https://storage.example.com/story.jpg",
            media_type="IMAGE",
        )

        assert container_id == "story_container_img"
        ig_api.client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_story_container_video(self, ig_api):
        """Creating a video story container returns a container ID."""
        mock_response = httpx.Response(
            200,
            json={"id": "story_container_vid"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig_id/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        container_id = await ig_api.create_story_container(
            ig_account_id="17841400123456789",
            media_url="https://storage.example.com/story.mp4",
            media_type="VIDEO",
        )

        assert container_id == "story_container_vid"

    @pytest.mark.asyncio
    async def test_create_story_container_sends_stories_media_type(self, ig_api):
        """Story container request includes media_type=STORIES."""
        mock_response = httpx.Response(
            200,
            json={"id": "story_c"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_story_container(
            ig_account_id="ig_id",
            media_url="https://example.com/story.jpg",
            media_type="IMAGE",
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["media_type"] == "STORIES"

    @pytest.mark.asyncio
    async def test_create_story_container_image_uses_image_url(self, ig_api):
        """Image story sets image_url in the request data."""
        mock_response = httpx.Response(
            200,
            json={"id": "story_img_url"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_story_container(
            ig_account_id="ig_id",
            media_url="https://example.com/story_photo.jpg",
            media_type="IMAGE",
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["image_url"] == "https://example.com/story_photo.jpg"
        assert "video_url" not in data_arg

    @pytest.mark.asyncio
    async def test_create_story_container_video_uses_video_url(self, ig_api):
        """Video story sets video_url in the request data."""
        mock_response = httpx.Response(
            200,
            json={"id": "story_vid_url"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_story_container(
            ig_account_id="ig_id",
            media_url="https://example.com/story_video.mp4",
            media_type="VIDEO",
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["video_url"] == "https://example.com/story_video.mp4"
        assert "image_url" not in data_arg

    @pytest.mark.asyncio
    async def test_create_story_container_default_image_type(self, ig_api):
        """Default media_type is IMAGE."""
        mock_response = httpx.Response(
            200,
            json={"id": "story_def"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_story_container(
            ig_account_id="ig_id",
            media_url="https://example.com/story.jpg",
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg.get("image_url") == "https://example.com/story.jpg"

    @pytest.mark.asyncio
    async def test_create_story_container_api_error(self, ig_api):
        """API error during story container creation raises InstagramGraphAPIError."""
        error_response = httpx.Response(
            400,
            json={"error": {"message": "Story image too small", "type": "OAuthException", "code": 100}},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Bad Request", request=error_response.request, response=error_response
        ))

        with pytest.raises(InstagramGraphAPIError, match="Story image too small"):
            await ig_api.create_story_container(
                ig_account_id="ig_id",
                media_url="https://example.com/tiny.jpg",
            )


# ---------------------------------------------------------------------------
# _publish_to_instagram unit tests (story path)
# ---------------------------------------------------------------------------

class TestPublishToInstagramStory:
    """Tests for the _publish_to_instagram helper with story posts."""

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_story_image_publish_success(
        self, mock_decrypt, mock_post_story, mock_clip_story_image, mock_account
    ):
        """Successfully publishing an image story returns platform_post_id and URL."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance

            mock_api_instance.create_story_container = AsyncMock(
                return_value="story_container_1"
            )
            mock_api_instance.publish_container = AsyncMock(return_value="media_story_1")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "id": "media_story_1",
                "permalink": "https://www.instagram.com/stories/testuser/STORY123/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(
                mock_post_story, mock_clip_story_image, mock_account
            )

            assert result["platform_post_id"] == "media_story_1"
            assert "STORY123" in result["platform_url"]

            # Verify story container was created
            mock_api_instance.create_story_container.assert_called_once()

            # Verify it used IMAGE type
            create_kwargs = mock_api_instance.create_story_container.call_args
            assert create_kwargs.kwargs["media_type"] == "IMAGE"

            # Verify no video processing polling happened
            mock_api_instance.check_container_status.assert_not_called()

            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_story_video_publish_success(
        self, mock_sleep, mock_decrypt, mock_post_story, mock_clip_story_video, mock_account
    ):
        """Successfully publishing a video story waits for processing then publishes."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance

            mock_api_instance.create_story_container = AsyncMock(
                return_value="story_video_container"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "FINISHED"}
            )
            mock_api_instance.publish_container = AsyncMock(return_value="media_story_vid")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "id": "media_story_vid",
                "permalink": "https://www.instagram.com/stories/testuser/STORYVID/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(
                mock_post_story, mock_clip_story_video, mock_account
            )

            assert result["platform_post_id"] == "media_story_vid"

            # Verify story container was created with VIDEO type
            create_kwargs = mock_api_instance.create_story_container.call_args
            assert create_kwargs.kwargs["media_type"] == "VIDEO"

            # Verify video processing was checked
            mock_api_instance.check_container_status.assert_called_once_with(
                "story_video_container"
            )

            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_story_video_waits_for_processing(
        self, mock_sleep, mock_decrypt, mock_post_story, mock_clip_story_video, mock_account
    ):
        """Video story waits while processing is IN_PROGRESS."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance

            mock_api_instance.create_story_container = AsyncMock(
                return_value="story_slow"
            )
            mock_api_instance.check_container_status = AsyncMock(
                side_effect=[
                    {"status_code": "IN_PROGRESS"},
                    {"status_code": "IN_PROGRESS"},
                    {"status_code": "FINISHED"},
                ]
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m_story")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://instagram.com/stories/user/X/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(
                mock_post_story, mock_clip_story_video, mock_account
            )

            assert result["platform_post_id"] == "m_story"
            assert mock_api_instance.check_container_status.call_count == 3
            assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_story_video_processing_error(
        self, mock_sleep, mock_decrypt, mock_post_story, mock_clip_story_video, mock_account
    ):
        """Video story processing ERROR raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_story_container = AsyncMock(
                return_value="story_err"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "ERROR", "status": "Story video too long"}
            )
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="Story video processing failed"):
                await _publish_to_instagram(
                    mock_post_story, mock_clip_story_video, mock_account
                )

            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_story_video_processing_timeout(
        self, mock_sleep, mock_decrypt, mock_post_story, mock_clip_story_video, mock_account
    ):
        """Video story processing timeout raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_story_container = AsyncMock(
                return_value="story_timeout"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "IN_PROGRESS"}
            )
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="Story video processing timeout"):
                await _publish_to_instagram(
                    mock_post_story, mock_clip_story_video, mock_account
                )

            assert mock_api_instance.check_container_status.call_count == 30
            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_story_publish_default_image_type(
        self, mock_decrypt, mock_post_story, mock_account
    ):
        """Story without explicit story_media_type defaults to IMAGE."""
        from app.services.social_service import _publish_to_instagram

        clip = SimpleNamespace(
            id=12,
            media_url="https://storage.example.com/story_default.jpg",
            media_type="story",
            # No story_media_type attribute
        )

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_story_container = AsyncMock(
                return_value="story_def_c"
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m_def_story")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://instagram.com/stories/user/DEF/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(mock_post_story, clip, mock_account)

            create_kwargs = mock_api_instance.create_story_container.call_args
            assert create_kwargs.kwargs["media_type"] == "IMAGE"

            # No video processing check for image stories
            mock_api_instance.check_container_status.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_story_publish_api_error_propagates(
        self, mock_decrypt, mock_post_story, mock_clip_story_image, mock_account
    ):
        """API error during story container creation propagates as ValueError."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_story_container = AsyncMock(
                side_effect=InstagramGraphAPIError("Story dimensions invalid")
            )
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="Instagram API error.*Story dimensions invalid"):
                await _publish_to_instagram(
                    mock_post_story, mock_clip_story_image, mock_account
                )

            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value=None)
    async def test_story_publish_invalid_token(
        self, mock_decrypt, mock_post_story, mock_clip_story_image, mock_account
    ):
        """Invalid (None) access token raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        with pytest.raises(ValueError, match="Invalid access token"):
            await _publish_to_instagram(
                mock_post_story, mock_clip_story_image, mock_account
            )

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_story_publish_missing_ig_account_id(
        self, mock_decrypt, mock_post_story, mock_clip_story_image, mock_account
    ):
        """Missing IG business account ID raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        mock_account.meta_info = {}

        with pytest.raises(ValueError, match="Instagram Business Account ID not found"):
            await _publish_to_instagram(
                mock_post_story, mock_clip_story_image, mock_account
            )

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_story_publish_missing_media_url(
        self, mock_decrypt, mock_post_story, mock_account
    ):
        """Missing media_url on story clip raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        clip = SimpleNamespace(id=13, media_type="story")

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="does not have a media URL"):
                await _publish_to_instagram(mock_post_story, clip, mock_account)

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_story_publish_with_caption(
        self, mock_decrypt, mock_clip_story_image, mock_account
    ):
        """Stories don't use captions in the container but the flow still works."""
        from app.services.social_service import _publish_to_instagram

        post = SimpleNamespace(
            id=41,
            user_id=1,
            clip_id=10,
            platform=SimpleNamespace(value="instagram"),
            caption="Story caption (not used by IG API)",
            hashtags=json.dumps(["#story"]),
            status="publishing",
        )

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_story_container = AsyncMock(
                return_value="story_cap_c"
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m_cap")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://instagram.com/stories/user/CAP/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(post, mock_clip_story_image, mock_account)

            assert result["platform_post_id"] == "m_cap"
            # Story container was created (captions go to story overlay, not API)
            mock_api_instance.create_story_container.assert_called_once()


# ---------------------------------------------------------------------------
# publish_post end-to-end tests (story to Instagram)
# ---------------------------------------------------------------------------

class TestPublishPostStoryEndToEnd:
    """End-to-end tests for publish_post with Instagram story posts."""

    def _make_db_post(self, status="draft"):
        """Create a mock SocialPost DB object for story."""
        post = MagicMock()
        post.id = 40
        post.user_id = 1
        post.clip_id = 10
        post.platform = MagicMock()
        post.platform.value = "instagram"
        post.platform.__eq__ = lambda self, other: (
            getattr(other, 'value', other) == "instagram" or other == self
        )
        post.caption = "E2E story test"
        post.hashtags = None
        post.status = status
        post.published_at = None
        post.platform_post_id = None
        post.platform_url = None
        post.error_message = None
        return post

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="token")
    async def test_publish_post_story_image_success(self, mock_decrypt):
        """Full publish_post flow for an Instagram image story succeeds."""
        from app.services.social_service import publish_post, PostStatus, SocialPlatform

        db_post = self._make_db_post()
        db_post.platform = SocialPlatform.INSTAGRAM

        mock_clip = SimpleNamespace(
            id=10,
            media_url="https://storage.example.com/story.jpg",
            media_type="story",
            story_media_type="IMAGE",
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
            mock_api_instance.create_story_container = AsyncMock(
                return_value="story_e2e_c"
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m_story_e2e")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://www.instagram.com/stories/testuser/STORY_E2E/",
            })
            mock_api_instance.close = AsyncMock()

            result = await publish_post(mock_db, post_id=40)

            assert result["success"] is True
            assert result["post_id"] == 40
            assert "STORY_E2E" in result.get("platform_url", "")

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="token")
    @patch("app.services.social_service.asyncio.sleep", new_callable=AsyncMock)
    async def test_publish_post_story_video_success(self, mock_sleep, mock_decrypt):
        """Full publish_post flow for an Instagram video story succeeds."""
        from app.services.social_service import publish_post, PostStatus, SocialPlatform

        db_post = self._make_db_post()
        db_post.platform = SocialPlatform.INSTAGRAM

        mock_clip = SimpleNamespace(
            id=11,
            media_url="https://storage.example.com/story.mp4",
            media_type="story",
            story_media_type="VIDEO",
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
            mock_api_instance.create_story_container = AsyncMock(
                return_value="story_vid_e2e_c"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "FINISHED"}
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m_story_vid_e2e")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://www.instagram.com/stories/testuser/STORYVID_E2E/",
            })
            mock_api_instance.close = AsyncMock()

            result = await publish_post(mock_db, post_id=40)

            assert result["success"] is True
            assert result["post_id"] == 40
            assert "STORYVID_E2E" in result.get("platform_url", "")

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="token")
    async def test_publish_post_story_api_failure_marks_failed(self, mock_decrypt):
        """When story API fails, post status is set to FAILED."""
        from app.services.social_service import publish_post, PostStatus, SocialPlatform

        db_post = self._make_db_post()
        db_post.platform = SocialPlatform.INSTAGRAM

        mock_clip = SimpleNamespace(
            id=10,
            media_url="https://storage.example.com/story.jpg",
            media_type="story",
            story_media_type="IMAGE",
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
            mock_api_instance.create_story_container = AsyncMock(
                side_effect=InstagramGraphAPIError("Permission denied")
            )
            mock_api_instance.close = AsyncMock()

            result = await publish_post(mock_db, post_id=40)

            assert result["success"] is False
            assert "error" in result
            assert db_post.status == PostStatus.FAILED
            assert db_post.error_message is not None
