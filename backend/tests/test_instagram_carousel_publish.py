"""
Tests for Instagram carousel (multi-image) publishing.

Covers:
- InstagramGraphAPI.create_carousel_container
- InstagramGraphAPI child container creation for carousel items
- _publish_to_instagram (carousel path)
- publish_post end-to-end (carousel to Instagram)
- Error scenarios (too few items, too many items, API failures, mixed media)
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
def mock_clip_carousel():
    """A clip-like object representing a carousel (multi-image)."""
    clip = SimpleNamespace(
        id=3,
        media_url="https://storage.example.com/images/cover.jpg",
        media_type="carousel",
        file_path="images/cover.jpg",
        carousel_media_urls=[
            "https://storage.example.com/images/photo1.jpg",
            "https://storage.example.com/images/photo2.jpg",
            "https://storage.example.com/images/photo3.jpg",
        ],
        carousel_media_types=["image", "image", "image"],
    )
    return clip


@pytest.fixture
def mock_clip_carousel_mixed():
    """A clip-like object representing a carousel with mixed image and video."""
    clip = SimpleNamespace(
        id=4,
        media_url="https://storage.example.com/images/cover.jpg",
        media_type="carousel",
        file_path="images/cover.jpg",
        carousel_media_urls=[
            "https://storage.example.com/images/photo1.jpg",
            "https://storage.example.com/videos/clip1.mp4",
            "https://storage.example.com/images/photo2.jpg",
        ],
        carousel_media_types=["image", "video", "image"],
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
def mock_post_carousel():
    """A SocialPost-like object for carousel publishing."""
    post = SimpleNamespace(
        id=20,
        user_id=1,
        clip_id=3,
        platform=SimpleNamespace(value="instagram"),
        caption="Check out this gallery!",
        hashtags=json.dumps(["#gallery", "#carousel", "#photography"]),
        status="publishing",
    )
    return post


# ---------------------------------------------------------------------------
# InstagramGraphAPI unit tests – carousel container
# ---------------------------------------------------------------------------

class TestCreateCarouselContainer:
    """Tests for InstagramGraphAPI.create_carousel_container"""

    @pytest.mark.asyncio
    async def test_create_carousel_container_basic(self, ig_api):
        """Creating a carousel container returns a container ID."""
        mock_response = httpx.Response(
            200,
            json={"id": "carousel_container_123"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig_id/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        container_id = await ig_api.create_carousel_container(
            ig_account_id="17841400123456789",
            children=["child_1", "child_2", "child_3"],
            caption="Multi-image post",
        )

        assert container_id == "carousel_container_123"
        ig_api.client.post.assert_called_once()
        call_kwargs = ig_api.client.post.call_args
        assert "17841400123456789/media" in call_kwargs.args[0]

    @pytest.mark.asyncio
    async def test_create_carousel_container_sends_media_type(self, ig_api):
        """Carousel container request includes media_type=CAROUSEL."""
        mock_response = httpx.Response(
            200,
            json={"id": "carousel_c"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_carousel_container(
            ig_account_id="ig_id",
            children=["c1", "c2"],
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["media_type"] == "CAROUSEL"

    @pytest.mark.asyncio
    async def test_create_carousel_container_children_comma_separated(self, ig_api):
        """Children IDs are sent as a comma-separated string."""
        mock_response = httpx.Response(
            200,
            json={"id": "carousel_c"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_carousel_container(
            ig_account_id="ig_id",
            children=["child_a", "child_b", "child_c"],
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["children"] == "child_a,child_b,child_c"

    @pytest.mark.asyncio
    async def test_create_carousel_container_with_caption(self, ig_api):
        """Caption is included in the carousel container request."""
        mock_response = httpx.Response(
            200,
            json={"id": "carousel_cap"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_carousel_container(
            ig_account_id="ig_id",
            children=["c1", "c2"],
            caption="Beautiful gallery",
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["caption"] == "Beautiful gallery"

    @pytest.mark.asyncio
    async def test_create_carousel_container_no_caption(self, ig_api):
        """Carousel container without caption omits it from the request."""
        mock_response = httpx.Response(
            200,
            json={"id": "carousel_nc"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_carousel_container(
            ig_account_id="ig_id",
            children=["c1", "c2"],
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert "caption" not in data_arg

    @pytest.mark.asyncio
    async def test_create_carousel_container_with_location(self, ig_api):
        """Location ID is included in the carousel container request."""
        mock_response = httpx.Response(
            200,
            json={"id": "carousel_loc"},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(return_value=mock_response)

        await ig_api.create_carousel_container(
            ig_account_id="ig_id",
            children=["c1", "c2"],
            location_id="loc_789",
        )

        call_kwargs = ig_api.client.post.call_args
        data_arg = call_kwargs.kwargs.get("data", {})
        assert data_arg["location_id"] == "loc_789"

    @pytest.mark.asyncio
    async def test_create_carousel_container_api_error(self, ig_api):
        """API error during carousel container creation raises InstagramGraphAPIError."""
        error_response = httpx.Response(
            400,
            json={"error": {"message": "Invalid children IDs", "type": "OAuthException", "code": 100}},
            request=httpx.Request("POST", "https://graph.facebook.com/v18.0/ig/media"),
        )
        ig_api.client = AsyncMock()
        ig_api.client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Bad Request", request=error_response.request, response=error_response
        ))

        with pytest.raises(InstagramGraphAPIError, match="Invalid children IDs"):
            await ig_api.create_carousel_container(
                ig_account_id="ig_id",
                children=["bad_c1", "bad_c2"],
            )


# ---------------------------------------------------------------------------
# _publish_to_instagram unit tests (carousel path)
# ---------------------------------------------------------------------------

class TestPublishToInstagramCarousel:
    """Tests for the _publish_to_instagram helper with carousel posts."""

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_carousel_publish_success(
        self, mock_decrypt, mock_post_carousel, mock_clip_carousel, mock_account
    ):
        """Successfully publishing a carousel returns platform_post_id and URL."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance

            # Child container creation returns unique IDs
            mock_api_instance.create_image_container = AsyncMock(
                side_effect=["child_c1", "child_c2", "child_c3"]
            )
            mock_api_instance.create_carousel_container = AsyncMock(
                return_value="carousel_container_1"
            )
            mock_api_instance.publish_container = AsyncMock(return_value="media_carousel_1")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "id": "media_carousel_1",
                "permalink": "https://www.instagram.com/p/CAROUSEL123/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(
                mock_post_carousel, mock_clip_carousel, mock_account
            )

            assert result["platform_post_id"] == "media_carousel_1"
            assert result["platform_url"] == "https://www.instagram.com/p/CAROUSEL123/"

            # Verify 3 child image containers were created
            assert mock_api_instance.create_image_container.call_count == 3

            # Verify carousel container was created with children
            mock_api_instance.create_carousel_container.assert_called_once()
            call_kwargs = mock_api_instance.create_carousel_container.call_args
            assert call_kwargs.kwargs["children"] == ["child_c1", "child_c2", "child_c3"]

            # Verify the container was published
            mock_api_instance.publish_container.assert_called_once_with(
                ig_account_id="17841400123456789",
                creation_id="carousel_container_1",
            )

            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_carousel_publish_caption_with_hashtags(
        self, mock_decrypt, mock_post_carousel, mock_clip_carousel, mock_account
    ):
        """Carousel caption includes appended hashtags on parent container."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_image_container = AsyncMock(
                side_effect=["c1", "c2", "c3"]
            )
            mock_api_instance.create_carousel_container = AsyncMock(
                return_value="carousel_c"
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m1")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://www.instagram.com/p/X/",
            })
            mock_api_instance.close = AsyncMock()

            await _publish_to_instagram(
                mock_post_carousel, mock_clip_carousel, mock_account
            )

            # Caption should be on the carousel container, not children
            carousel_kwargs = mock_api_instance.create_carousel_container.call_args
            caption_sent = carousel_kwargs.kwargs.get("caption", "")
            assert "#gallery" in caption_sent
            assert "#carousel" in caption_sent
            assert "Check out this gallery!" in caption_sent

            # Children should NOT have captions
            for call in mock_api_instance.create_image_container.call_args_list:
                assert "caption" not in call.kwargs

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_carousel_publish_mixed_media(
        self, mock_decrypt, mock_post_carousel, mock_clip_carousel_mixed, mock_account
    ):
        """Carousel with mixed image and video items creates correct containers."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance

            mock_api_instance.create_image_container = AsyncMock(
                side_effect=["img_child_1", "img_child_2"]
            )
            mock_api_instance.create_video_container = AsyncMock(
                return_value="vid_child_1"
            )
            mock_api_instance.check_container_status = AsyncMock(
                return_value={"status_code": "FINISHED"}
            )
            mock_api_instance.create_carousel_container = AsyncMock(
                return_value="mixed_carousel_c"
            )
            mock_api_instance.publish_container = AsyncMock(return_value="media_mixed")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://www.instagram.com/p/MIXED/",
            })
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(
                mock_post_carousel, mock_clip_carousel_mixed, mock_account
            )

            assert result["platform_post_id"] == "media_mixed"

            # Verify 2 image containers and 1 video container
            assert mock_api_instance.create_image_container.call_count == 2
            assert mock_api_instance.create_video_container.call_count == 1

            # Verify video container status was checked
            mock_api_instance.check_container_status.assert_called_once_with("vid_child_1")

            # Verify carousel children order: img, vid, img
            carousel_kwargs = mock_api_instance.create_carousel_container.call_args
            assert carousel_kwargs.kwargs["children"] == [
                "img_child_1", "vid_child_1", "img_child_2"
            ]

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_carousel_publish_too_few_items(
        self, mock_decrypt, mock_post_carousel, mock_account
    ):
        """Carousel with fewer than 2 items raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        clip = SimpleNamespace(
            id=5,
            media_url="https://storage.example.com/images/single.jpg",
            media_type="carousel",
            carousel_media_urls=["https://storage.example.com/images/single.jpg"],
            carousel_media_types=["image"],
        )

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="at least 2 media items"):
                await _publish_to_instagram(mock_post_carousel, clip, mock_account)

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_carousel_publish_too_many_items(
        self, mock_decrypt, mock_post_carousel, mock_account
    ):
        """Carousel with more than 10 items raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        clip = SimpleNamespace(
            id=6,
            media_url="https://storage.example.com/images/cover.jpg",
            media_type="carousel",
            carousel_media_urls=[f"https://storage.example.com/img{i}.jpg" for i in range(11)],
            carousel_media_types=["image"] * 11,
        )

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="maximum of 10 media items"):
                await _publish_to_instagram(mock_post_carousel, clip, mock_account)

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_carousel_publish_no_carousel_urls(
        self, mock_decrypt, mock_post_carousel, mock_account
    ):
        """Carousel with no carousel_media_urls raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        clip = SimpleNamespace(
            id=7,
            media_url="https://storage.example.com/images/cover.jpg",
            media_type="carousel",
        )

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="at least 2 media items"):
                await _publish_to_instagram(mock_post_carousel, clip, mock_account)

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_carousel_publish_child_creation_api_error(
        self, mock_decrypt, mock_post_carousel, mock_clip_carousel, mock_account
    ):
        """API error during child container creation propagates as ValueError."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_image_container = AsyncMock(
                side_effect=InstagramGraphAPIError("Image too large")
            )
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="Instagram API error.*Image too large"):
                await _publish_to_instagram(
                    mock_post_carousel, mock_clip_carousel, mock_account
                )

            mock_api_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_carousel_publish_carousel_container_api_error(
        self, mock_decrypt, mock_post_carousel, mock_clip_carousel, mock_account
    ):
        """API error during carousel container creation propagates as ValueError."""
        from app.services.social_service import _publish_to_instagram

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_image_container = AsyncMock(
                side_effect=["c1", "c2", "c3"]
            )
            mock_api_instance.create_carousel_container = AsyncMock(
                side_effect=InstagramGraphAPIError("Too many children")
            )
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="Instagram API error.*Too many children"):
                await _publish_to_instagram(
                    mock_post_carousel, mock_clip_carousel, mock_account
                )

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_carousel_publish_unsupported_child_type(
        self, mock_decrypt, mock_post_carousel, mock_account
    ):
        """Unsupported child media type raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        clip = SimpleNamespace(
            id=8,
            media_url="https://storage.example.com/cover.jpg",
            media_type="carousel",
            carousel_media_urls=[
                "https://storage.example.com/audio1.mp3",
                "https://storage.example.com/audio2.mp3",
            ],
            carousel_media_types=["audio", "audio"],
        )

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.close = AsyncMock()

            with pytest.raises(ValueError, match="Unsupported carousel child media type"):
                await _publish_to_instagram(mock_post_carousel, clip, mock_account)

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_carousel_publish_default_child_type_is_image(
        self, mock_decrypt, mock_post_carousel, mock_account
    ):
        """When carousel_media_types is shorter than URLs, default type is image."""
        from app.services.social_service import _publish_to_instagram

        clip = SimpleNamespace(
            id=9,
            media_url="https://storage.example.com/cover.jpg",
            media_type="carousel",
            carousel_media_urls=[
                "https://storage.example.com/img1.jpg",
                "https://storage.example.com/img2.jpg",
                "https://storage.example.com/img3.jpg",
            ],
            carousel_media_types=["image"],  # Only 1 type for 3 URLs
        )

        with patch("app.services.social_service.InstagramGraphAPI") as MockAPI:
            mock_api_instance = AsyncMock()
            MockAPI.return_value = mock_api_instance
            mock_api_instance.create_image_container = AsyncMock(
                side_effect=["c1", "c2", "c3"]
            )
            mock_api_instance.create_carousel_container = AsyncMock(
                return_value="carousel_def"
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m_def")
            mock_api_instance.get_media_details = AsyncMock(
                return_value={"permalink": "https://instagram.com/p/DEF/"}
            )
            mock_api_instance.close = AsyncMock()

            result = await _publish_to_instagram(mock_post_carousel, clip, mock_account)

            # All 3 should use image container (default)
            assert mock_api_instance.create_image_container.call_count == 3
            assert mock_api_instance.create_video_container.call_count == 0

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value=None)
    async def test_carousel_publish_invalid_token(
        self, mock_decrypt, mock_post_carousel, mock_clip_carousel, mock_account
    ):
        """Invalid (None) access token raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        with pytest.raises(ValueError, match="Invalid access token"):
            await _publish_to_instagram(
                mock_post_carousel, mock_clip_carousel, mock_account
            )

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="decrypted-token")
    async def test_carousel_publish_missing_ig_account_id(
        self, mock_decrypt, mock_post_carousel, mock_clip_carousel, mock_account
    ):
        """Missing IG business account ID raises ValueError."""
        from app.services.social_service import _publish_to_instagram

        mock_account.meta_info = {}

        with pytest.raises(ValueError, match="Instagram Business Account ID not found"):
            await _publish_to_instagram(
                mock_post_carousel, mock_clip_carousel, mock_account
            )


# ---------------------------------------------------------------------------
# publish_post end-to-end tests (carousel to Instagram)
# ---------------------------------------------------------------------------

class TestPublishPostCarouselEndToEnd:
    """End-to-end tests for publish_post with Instagram carousel posts."""

    def _make_db_post(self, status="draft"):
        """Create a mock SocialPost DB object for carousel."""
        post = MagicMock()
        post.id = 20
        post.user_id = 1
        post.clip_id = 3
        post.platform = MagicMock()
        post.platform.value = "instagram"
        post.platform.__eq__ = lambda self, other: (
            getattr(other, 'value', other) == "instagram" or other == self
        )
        post.caption = "E2E carousel test"
        post.hashtags = json.dumps(["#test", "#carousel"])
        post.status = status
        post.published_at = None
        post.platform_post_id = None
        post.platform_url = None
        post.error_message = None
        return post

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="token")
    async def test_publish_post_carousel_success(self, mock_decrypt):
        """Full publish_post flow for an Instagram carousel succeeds."""
        from app.services.social_service import publish_post, PostStatus, SocialPlatform

        db_post = self._make_db_post()
        db_post.platform = SocialPlatform.INSTAGRAM

        mock_clip = SimpleNamespace(
            id=3,
            media_url="https://storage.example.com/cover.jpg",
            media_type="carousel",
            carousel_media_urls=[
                "https://storage.example.com/img1.jpg",
                "https://storage.example.com/img2.jpg",
            ],
            carousel_media_types=["image", "image"],
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
            mock_api_instance.create_image_container = AsyncMock(
                side_effect=["child_1", "child_2"]
            )
            mock_api_instance.create_carousel_container = AsyncMock(
                return_value="carousel_e2e"
            )
            mock_api_instance.publish_container = AsyncMock(return_value="m_carousel_e2e")
            mock_api_instance.get_media_details = AsyncMock(return_value={
                "permalink": "https://www.instagram.com/p/CAROUSEL_E2E/",
            })
            mock_api_instance.close = AsyncMock()

            result = await publish_post(mock_db, post_id=20)

            assert result["success"] is True
            assert result["post_id"] == 20
            assert "CAROUSEL_E2E" in result.get("platform_url", "")

    @pytest.mark.asyncio
    @patch("app.services.social_service.decrypt_token", return_value="token")
    async def test_publish_post_carousel_api_failure_marks_failed(self, mock_decrypt):
        """When carousel API fails, post status is set to FAILED."""
        from app.services.social_service import publish_post, PostStatus, SocialPlatform

        db_post = self._make_db_post()
        db_post.platform = SocialPlatform.INSTAGRAM

        mock_clip = SimpleNamespace(
            id=3,
            media_url="https://storage.example.com/cover.jpg",
            media_type="carousel",
            carousel_media_urls=[
                "https://storage.example.com/img1.jpg",
                "https://storage.example.com/img2.jpg",
            ],
            carousel_media_types=["image", "image"],
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
                side_effect=InstagramGraphAPIError("Rate limit exceeded")
            )
            mock_api_instance.close = AsyncMock()

            result = await publish_post(mock_db, post_id=20)

            assert result["success"] is False
            assert "error" in result
            assert db_post.status == PostStatus.FAILED
            assert db_post.error_message is not None
