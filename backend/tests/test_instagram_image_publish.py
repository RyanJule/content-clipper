"""
Tests for Instagram single image publishing.

Covers:
- InstagramGraphAPI.create_image_container
- InstagramGraphAPI.publish_container
- InstagramGraphAPI.get_media_details
- _publish_to_instagram (image path)
- publish_post end-to-end (image to Instagram)
- Error scenarios (bad token, missing account ID, API failures, missing media URL)
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
def mock_clip_image():
    """A clip-like object representing an image."""
    clip = SimpleNamespace(
        id=1,
        media_url="https://storage.example.com/images/photo.jpg",
        media_type="image",
        file_path="images/photo.jpg",
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
def mock_post_image():
    """A SocialPost-like object for image publishing."""
    post = SimpleNamespace(
        id=10,
        user_id=1,
        clip_id=1,
        platform=SimpleNamespace(value="instagram"),
        caption="Check out this photo!",
        hashtags=json.dumps(["#photography", "#nature"]),
        status="publishing",
    )
    return post


# ---------------------------------------------------------------------------
# InstagramGraphAPI unit tests
# ---------------------------------------------------------------------------

class TestCreateImageContainer:
    """Tests for InstagramGraphAPI.create_image_container"""

    @pytest.mark.asyncio
    async def test_create_image_container_basic(self, ig_api):
        """Creating an image container returns a container ID."""
        mock_response = httpx.Response(
            200,
            json={"id": "container_123"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig_id/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        container_id = await ig_api.create_image_container(
            ig_account_id="17841400123456789",
            image_url="https://storage.example.com/photo.jpg",
            caption="Test caption",
        )

        assert container_id == "container_123"
        ig_api.client.post.assert_called_once()
        call_kwargs = ig_api.client.post.call_args
        assert "17841400123456789/media" in call_kwargs.args[0]

    @pytest.mark.asyncio
    async def test_create_image_container_with_location(self, ig_api):
        """Creating an image container with location_id passes it through."""
        mock_response = httpx.Response(
            200,
            json={"id": "container_loc"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        container_id = await ig_api.create_image_container(
            ig_account_id="ig_id",
            image_url="https://example.com/photo.jpg",
            caption="With location",
            location_id="loc_456",
        )

        assert container_id == "container_loc"
        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["location_id"] == "loc_456"

    @pytest.mark.asyncio
    async def test_create_image_container_with_user_tags(self, ig_api):
        """Creating an image container with user_tags passes them through."""
        mock_response = httpx.Response(
            200,
            json={"id": "container_tags"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        tags = [{"username": "friend1", "x": 0.5, "y": 0.5}]
        container_id = await ig_api.create_image_container(
            ig_account_id="ig_id",
            image_url="https://example.com/photo.jpg",
            user_tags=tags,
        )

        assert container_id == "container_tags"
        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["user_tags"] == tags

    @pytest.mark.asyncio
    async def test_create_image_container_no_caption(self, ig_api):
        """Creating an image container without caption omits it from request."""
        mock_response = httpx.Response(
            200,
            json={"id": "container_no_cap"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        container_id = await ig_api.create_image_container(
            ig_account_id="ig_id",
            image_url="https://example.com/photo.jpg",
        )

        assert container_id == "container_no_cap"
        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert "caption" not in data_arg

    @pytest.mark.asyncio
    async def test_create_image_container_api_error(self, ig_api):
        """API error during container creation raises InstagramGraphAPIError."""
        error_response = httpx.Response(
            400,
            json={"error": {"message": "Invalid image URL", "type": "OAuthException", "code": 100}},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Bad Request", request=error_response.request, response=error_response
        ))

        with pytest.raises(InstagramGraphAPIError, match="Invalid image URL"):
            await ig_api.create_image_container(
                ig_account_id="ig_id",
                image_url="https://example.com/bad.jpg",
            )


class TestPublishContainer:
    """Tests for InstagramGraphAPI.publish_container"""

    @pytest.mark.asyncio
    async def test_publish_container_success(self, ig_api):
        """Publishing a container returns the media ID."""
        mock_response = httpx.Response(
            200,
            json={"id": "media_789"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media_publish"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        media_id = await ig_api.publish_container(
            ig_account_id="17841400123456789",
            creation_id="container_123",
        )

        assert media_id == "media_789"
        call_kwargs = ig_api.client.post.call_args
        assert "17841400123456789/media_publish" in call_kwargs.args[0]

    @pytest.mark.asyncio
    async def test_publish_container_api_error(self, ig_api):
        """API error during publish raises InstagramGraphAPIError."""
        error_response = httpx.Response(
            400,
            json={"error": {"message": "Container not ready"}},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media_publish"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Bad Request", request=error_response.request, response=error_response
        ))

        with pytest.raises(InstagramGraphAPIError, match="Container not ready"):
            await ig_api.publish_container(
                ig_account_id="ig_id",
                creation_id="bad_container",
            )


class TestGetMediaDetails:
    """Tests for InstagramGraphAPI.get_media_details"""

    @pytest.mark.asyncio
    async def test_get_media_details_success(self, ig_api):
        """Getting media details returns permalink and metadata."""
        mock_response = httpx.Response(
            200,
            json={
                "id": "media_789",
                "permalink": "https://www.instagram.com/p/ABC123/",
                "media_type": "IMAGE",
                "caption": "Test caption",
                "timestamp": "2024-01-15T12:00:00+0000",
            },
            request=httpx.Request("GET", "https://graph.facebook.com/v18.0/media_789"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.get = AsyncMock(return_value=mock_response)

        details = await ig_api.get_media_details("media_789")

        assert details["permalink"] == "https://www.instagram.com/p/ABC123/"
        assert details["media_type"] == "IMAGE"
        assert details["id"] == "media_789"


# ---------------------------------------------------------------------------
# _publish_to_instagram unit tests (image path)
# ---------------------------------------------------------------------------

class TestPublishToInstagram:
    """Tests for the _publish_to_instagram helper in social_service."""

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_image_publish_success(self, mock_decrypt, mock_post_image, mock_clip_image, mock_account):
        """Successfully publishing an image returns platform_post_id and URL."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance

            mock_api_instance.create_image_container = AsyncMock(return_value="container_img_1")
            mock_api_instance.publish_container = AsyncMock(return_value="media_img_1")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "id": "media_img_1",
                "permalink": "https://www.instagram.com/p/IMG123/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(mock_post_image, mock_clip_image, mock_account)

            assert result["platform_post_id"] == "media_img_1"
            assert result["platform_url"] == "https://www.instagram.com/p/IMG123/"

            # Verify image container was created (not video)
            mock_api_instance.create_image_container.assert_called_once()
            mock_api_instance.create_video_container.assert_not_called()

            # Verify the container was published
            mock_api_instance.publish_container.assert_called_once_with(
                ig_account_id="17841400123456789",
                creation_id="container_img_1",
            )

            # Verify cleanup
            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_image_publish_caption_with_hashtags(self, mock_decrypt, mock_post_image, mock_clip_image, mock_account):
        """Caption includes appended hashtags."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_image_container = AsyncMock(return_value="container_1")
            mock_api_instance.publish_container = AsyncMock(return_value="media_1")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://www.instagram.com/p/X/",
            })
            mock_api_instance.close = AsyncMock()

            await _publish_to_instagram(mock_post_image, mock_clip_image, mock_account)

            call_kwargs = mock_api_instance.create_image_container.call_args
            caption_sent = call_kwargs.kwargs.get("caption", "")
            assert "#photography" in caption_sent
            assert "#nature" in caption_sent
            assert "Check out this photo!" in caption_sent

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value=None)
    async def test_image_publish_invalid_token(self, mock_decrypt, mock_post_image, mock_clip_image, mock_account):
        """Invalid (None) access token raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        with pytest.raises(ValueError, match="Invalid access token"):
            await _publish_to_instagram(mock_post_image, mock_clip_image, mock_account)

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_image_publish_missing_ig_account_id(self, mock_decrypt, mock_post_image, mock_clip_image, mock_account):
        """Missing IG business account ID raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        mock_account.meta_info = {}  # No instagram_business_account_id

        with pytest.raises(ValueError, match="Instagram Business Account ID not found"):
            await _publish_to_instagram(mock_post_image, mock_clip_image, mock_account)

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_image_publish_missing_media_url(self, mock_decrypt, mock_post_image, mock_clip_image, mock_account):
        """Missing media_url on clip raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        # Remove the media_url attribute
        del mock_clip_image.media_url

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="does not have a media URL"):
                await _publish_to_instagram(mock_post_image, mock_clip_image, mock_account)

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_image_publish_api_error_propagates(self, mock_decrypt, mock_post_image, mock_clip_image, mock_account):
        """InstagramGraphAPIError during container creation propagates as ValueError."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_image_container = AsyncMock(
                side_effect=InstagramGraphAPIError("Rate limit exceeded")
            )
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="Instagram API error.*Rate limit exceeded"):
                await _publish_to_instagram(mock_post_image, mock_clip_image, mock_account)

            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_image_publish_photo_media_type(self, mock_decrypt, mock_post_image, mock_account):
        """media_type='photo' also uses image container path."""
        from app.services.social_service import _publish_to_instagram

        clip = SimpleNamespace(
            id=2,
            media_url="https://storage.example.com/images/photo2.jpg",
            media_type="photo",
        )

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_image_container = AsyncMock(return_value="container_photo")
            mock_api_instance.publish_container = AsyncMock(return_value="media_photo")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://www.instagram.com/p/PHOTO/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(mock_post_image, clip, mock_account)

            assert result["platform_post_id"] == "media_photo"
            mock_api_instance.create_image_container.assert_called_once()
            mock_api_instance.create_video_container.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_image_publish_no_hashtags(self, mock_decrypt, mock_clip_image, mock_account):
        """Post without hashtags publishes caption as-is."""
        from app.services.social_service import _publish_to_instagram

        post = SimpleNamespace(
            id=11,
            user_id=1,
            clip_id=1,
            platform=SimpleNamespace(value="instagram"),
            caption="No tags here",
            hashtags=None,
            status="publishing",
        )

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_image_container = AsyncMock(return_value="c1")
            mock_api_instance.publish_container = AsyncMock(return_value="m1")
            mock_api_instance.get_media_details = AsyncMock(return_value={"permalink": "https://instagram.com/p/X/"})
            mock_api_instance.close = AsyncMock()

            await _publish_to_instagram(post, mock_clip_image, mock_account)

            call_kwargs = mock_api_instance.create_image_container.call_args
            caption_sent = call_kwargs.kwargs.get("caption", "")
            assert caption_sent == "No tags here"

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_image_publish_empty_caption(self, mock_decrypt, mock_clip_image, mock_account):
        """Post with empty caption and no hashtags sends empty string."""
        from app.services.social_service import _publish_to_instagram

        post = SimpleNamespace(
            id=12,
            user_id=1,
            clip_id=1,
            platform=SimpleNamespace(value="instagram"),
            caption=None,
            hashtags=None,
            status="publishing",
        )

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_image_container = AsyncMock(return_value="c1")
            mock_api_instance.publish_container = AsyncMock(return_value="m1")
            mock_api_instance.get_media_details = AsyncMock(return_value={"permalink": "https://instagram.com/p/Y/"})
            mock_api_instance.close = AsyncMock()

            await _publish_to_instagram(post, mock_clip_image, mock_account)

            call_kwargs = mock_api_instance.create_image_container.call_args
            # caption kwarg should be "" (empty string from `post.caption or ""`)
            caption_sent = call_kwargs.kwargs.get("caption", "")
            assert caption_sent == ""


# ---------------------------------------------------------------------------
# publish_post end-to-end tests (image to Instagram)
# ---------------------------------------------------------------------------

class TestPublishPostImageEndToEnd:
    """End-to-end tests for publish_post with Instagram image posts."""

    def _make_db_post(self, status="draft"):
        """Create a mock SocialPost DB object."""
        post = MagicMock()
        post.id = 10
        post.user_id = 1
        post.clip_id = 1
        post.platform = MagicMock()
        post.platform.value = "instagram"
        post.platform.__eq__ = lambda self, other: getattr(other, 'value', other) == "instagram" or other == self
        post.caption = "E2E image test"
        post.hashtags = json.dumps(["#test"])
        post.status = status
        post.published_at = None
        post.platform_post_id = None
        post.platform_url = None
        post.error_message = None
        return post

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="token")
    async def test_publish_post_image_success(self, mock_decrypt):
        """Full publish_post flow for an Instagram image succeeds."""
        from app.services.social_service import publish_post, PostStatus, SocialPlatform

        db_post = self._make_db_post()
        # Make platform comparison work for the if-branch
        db_post.platform = SocialPlatform.INSTAGRAM

        mock_clip = SimpleNamespace(
            id=1,
            media_url="https://storage.example.com/img.jpg",
            media_type="image",
        )
        mock_account = MagicMock()
        mock_account.access_token_enc = "enc-token"
        mock_account.meta_info = {"instagram_business_account_id": "ig_123"}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = db_post

        with patch("app.services.social_service.get_post", return_value=db_post), \
             patch("app.services.social_service.get_clip", return_value=mock_clip), \
             patch("app.services.social_service.InstagramGraphAPI") as MockAPI:

            # Set up account query
            mock_db.query.return_value.filter.return_value.first.return_value = mock_account

            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_image_container = AsyncMock(return_value="c_e2e")
            mock_api_instance.publish_container = AsyncMock(return_value="m_e2e")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://www.instagram.com/p/E2E123/",
            })
            mock_api_instance.close = AsyncMock()

            result = await publish_post(mock_db, post_id=10)

            assert result["success"] is True
            assert result["post_id"] == 10
            assert "E2E123" in result.get("platform_url", "")

    @pytest.mark.asyncio
    async def test_publish_post_not_found(self):
        """publish_post raises ValueError when post doesn't exist."""
        from app.services.social_service import publish_post

        mock_db = MagicMock()
        with patch("app.services.social_service.get_post", return_value=None):
            with pytest.raises(ValueError, match="Post not found"):
                await publish_post(mock_db, post_id=999)

    @pytest.mark.asyncio
    async def test_publish_post_already_published(self):
        """publish_post raises ValueError for already-published post."""
        from app.services.social_service import publish_post, PostStatus

        db_post = self._make_db_post()
        db_post.status = PostStatus.PUBLISHED

        mock_db = MagicMock()
        with patch("app.services.social_service.get_post", return_value=db_post):
            with pytest.raises(ValueError, match="already published"):
                await publish_post(mock_db, post_id=10)

    @pytest.mark.asyncio
    async def test_publish_post_no_account(self):
        """publish_post returns failure when no active account exists."""
        from app.services.social_service import publish_post, PostStatus, SocialPlatform

        db_post = self._make_db_post()
        db_post.platform = SocialPlatform.INSTAGRAM
        mock_clip = SimpleNamespace(id=1)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.social_service.get_post", return_value=db_post), \
             patch("app.services.social_service.get_clip", return_value=mock_clip):
            with pytest.raises(ValueError, match="No active instagram account"):
                await publish_post(mock_db, post_id=10)

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="token")
    async def test_publish_post_api_failure_marks_failed(self, mock_decrypt):
        """When Instagram API fails, post status is set to FAILED."""
        from app.services.social_service import publish_post, PostStatus, SocialPlatform

        db_post = self._make_db_post()
        db_post.platform = SocialPlatform.INSTAGRAM

        mock_clip = SimpleNamespace(
            id=1,
            media_url="https://storage.example.com/img.jpg",
            media_type="image",
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
            mock_api_instance.create_image_container = AsyncMock(
                side_effect=InstagramGraphAPIError("Server error")
            )
            mock_api_instance.close = AsyncMock()

            result = await publish_post(mock_db, post_id=10)

            assert result["success"] is False
            assert "error" in result
            assert db_post.status == PostStatus.FAILED
            assert db_post.error_message is not None
