"""Tests for image processing service and cover CDN API endpoints."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

from PIL import Image

from app.services.image_service import (
    generate_blurhash,
    resize_image,
    upload_to_s3,
)


def _make_test_image(width: int = 1000, height: int = 1500, fmt: str = "JPEG") -> bytes:
    """Create a minimal test image as bytes."""
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


class TestResizeImage:
    """Tests for the resize_image function."""

    def test_downscales_to_target_width(self):
        """Image wider than target should be resized down."""
        data = _make_test_image(1000, 1500)
        result = resize_image(data, 400)
        img = Image.open(io.BytesIO(result))
        assert img.width == 400
        assert img.height == 600  # proportional

    def test_does_not_upscale(self):
        """Image narrower than target should not be enlarged."""
        data = _make_test_image(200, 300)
        result = resize_image(data, 400)
        img = Image.open(io.BytesIO(result))
        assert img.width == 200
        assert img.height == 300

    def test_converts_rgba_to_rgb(self):
        """RGBA images should be converted to RGB for JPEG output."""
        img = Image.new("RGBA", (500, 500), color=(100, 150, 200, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()
        result = resize_image(data, 400)
        out_img = Image.open(io.BytesIO(result))
        assert out_img.mode == "RGB"
        assert out_img.width == 400

    def test_output_is_jpeg(self):
        """Output should always be JPEG bytes."""
        data = _make_test_image(500, 500)
        result = resize_image(data, 300)
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"


class TestGenerateBlurhash:
    """Tests for the generate_blurhash function."""

    def test_returns_non_empty_string(self):
        """Blurhash should be a non-empty string."""
        data = _make_test_image(200, 200)
        result = generate_blurhash(data)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_consistent_for_same_image(self):
        """Same image should produce the same blurhash."""
        data = _make_test_image(200, 200)
        h1 = generate_blurhash(data)
        h2 = generate_blurhash(data)
        assert h1 == h2

    def test_handles_rgba_input(self):
        """Should handle RGBA images without error."""
        img = Image.new("RGBA", (100, 100), color=(50, 100, 150, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = generate_blurhash(buf.getvalue())
        assert isinstance(result, str)
        assert len(result) > 0


class TestUploadToS3:
    """Tests for the upload_to_s3 function."""

    @patch("app.services.image_service.settings")
    def test_upload_returns_public_url(self, mock_settings):
        """Should return a constructed public URL after upload."""
        mock_settings.s3_bucket = "test-bucket"
        mock_settings.s3_region = "us-east-1"
        mock_settings.s3_public_url = ""
        mock_settings.s3_endpoint_url = ""

        mock_client = MagicMock()
        url = upload_to_s3(mock_client, "covers/book1/thumbnail.jpg", b"fake-data")

        mock_client.put_object.assert_called_once()
        assert "test-bucket" in url
        assert "covers/book1/thumbnail.jpg" in url

    @patch("app.services.image_service.settings")
    def test_upload_uses_public_url_when_set(self, mock_settings):
        """Should use s3_public_url when configured."""
        mock_settings.s3_bucket = "test-bucket"
        mock_settings.s3_public_url = "https://cdn.example.com"
        mock_settings.s3_endpoint_url = ""

        mock_client = MagicMock()
        url = upload_to_s3(mock_client, "covers/book1/card.jpg", b"data")
        assert url == "https://cdn.example.com/covers/book1/card.jpg"

    @patch("app.services.image_service.settings")
    def test_upload_uses_endpoint_url_for_minio(self, mock_settings):
        """Should use endpoint URL for MinIO-style access."""
        mock_settings.s3_bucket = "covers"
        mock_settings.s3_public_url = ""
        mock_settings.s3_endpoint_url = "http://localhost:9000"

        mock_client = MagicMock()
        url = upload_to_s3(mock_client, "covers/book1/detail.jpg", b"data")
        assert url == "http://localhost:9000/covers/covers/book1/detail.jpg"

    @patch("app.services.image_service.settings")
    def test_upload_sets_cache_control(self, mock_settings):
        """Should set a long Cache-Control header for immutable images."""
        mock_settings.s3_bucket = "b"
        mock_settings.s3_public_url = "https://cdn.example.com"
        mock_settings.s3_endpoint_url = ""

        mock_client = MagicMock()
        upload_to_s3(mock_client, "key.jpg", b"data")
        call_kwargs = mock_client.put_object.call_args.kwargs
        assert "max-age=31536000" in call_kwargs["CacheControl"]


class TestCoverProxyAPI:
    """Integration tests for cover-proxy and blurhash endpoints."""

    def test_cover_proxy_fallback_google_books(self, client, mock_google_books_search):
        """Cover proxy should return image content when no CDN cover exists."""
        # The mock_google_books_search fixture patches httpx.AsyncClient
        # but cover_proxy uses its own httpx client, so we patch that directly
        mock_img = b"x" * 6000  # > 5000 byte threshold
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = mock_img
        mock_resp.headers = {"content-type": "image/jpeg"}

        with patch("app.routers.books.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            resp = client.get(
                "/api/books/cover-proxy/test_book_1",
                follow_redirects=False,
            )
            assert resp.status_code == 200
            assert resp.headers["cache-control"] == "public, max-age=86400"

    def test_cover_proxy_redirects_to_cdn(self, client, db_session):
        """Cover proxy should redirect to CDN URL when BookCover exists."""
        from app.models import BookCover

        db_session.add(BookCover(
            book_id="cdn_book_1",
            thumbnail_url="https://cdn.example.com/covers/cdn_book_1/thumbnail.jpg",
            card_url="https://cdn.example.com/covers/cdn_book_1/card.jpg",
            detail_url="https://cdn.example.com/covers/cdn_book_1/detail.jpg",
            blurhash="LEHV6nWB2yk8pyo0adR*.7kCMdnj",
        ))
        db_session.commit()

        resp = client.get(
            "/api/books/cover-proxy/cdn_book_1",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "cdn.example.com" in resp.headers["location"]
        assert "detail.jpg" in resp.headers["location"]

    def test_cover_proxy_size_parameter(self, client, db_session):
        """Cover proxy should respect the size query parameter."""
        from app.models import BookCover

        db_session.add(BookCover(
            book_id="size_book_1",
            thumbnail_url="https://cdn.example.com/thumb.jpg",
            card_url="https://cdn.example.com/card.jpg",
            detail_url="https://cdn.example.com/detail.jpg",
            blurhash="LEHV6nWB2yk8pyo0adR*.7kCMdnj",
        ))
        db_session.commit()

        resp = client.get(
            "/api/books/cover-proxy/size_book_1?size=thumbnail",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "thumb.jpg" in resp.headers["location"]

    def test_blurhash_endpoint(self, client, db_session):
        """Blurhash endpoint should return cover data."""
        from app.models import BookCover

        db_session.add(BookCover(
            book_id="hash_book_1",
            thumbnail_url="https://cdn.example.com/thumb.jpg",
            card_url="https://cdn.example.com/card.jpg",
            detail_url="https://cdn.example.com/detail.jpg",
            blurhash="LEHV6nWB2yk8pyo0adR*.7kCMdnj",
        ))
        db_session.commit()

        resp = client.get("/api/books/cover/hash_book_1/blurhash")
        assert resp.status_code == 200
        data = resp.json()
        assert data["blurhash"] == "LEHV6nWB2yk8pyo0adR*.7kCMdnj"
        assert data["book_id"] == "hash_book_1"
        assert "thumbnail_url" in data
        assert "card_url" in data
        assert "detail_url" in data

    def test_blurhash_endpoint_not_found(self, client):
        """Blurhash endpoint should 404 when no cover exists."""
        resp = client.get("/api/books/cover/nonexistent/blurhash")
        assert resp.status_code == 404

    def test_discover_includes_blurhash(self, client, db_session, mock_google_books_search):
        """Discover endpoint should include blurhash data when covers exist."""
        from app.models import BookCover

        db_session.add(BookCover(
            book_id="book_1",
            thumbnail_url="https://cdn.example.com/book_1/thumb.jpg",
            card_url="https://cdn.example.com/book_1/card.jpg",
            detail_url="https://cdn.example.com/book_1/detail.jpg",
            blurhash="LKO2?U%2Tw=w]~RBVZRi};RPxuwH",
        ))
        db_session.commit()

        resp = client.get("/api/books/discover?category=fiction")
        assert resp.status_code == 200
        data = resp.json()
        # Find book_1 in results
        book1 = next((b for b in data["books"] if b["google_book_id"] == "book_1"), None)
        assert book1 is not None
        assert book1["blurhash"] == "LKO2?U%2Tw=w]~RBVZRi};RPxuwH"
        assert book1["card_cdn"] == "https://cdn.example.com/book_1/card.jpg"

    def test_book_detail_includes_blurhash(self, client, db_session, mock_google_book_detail):
        """Book detail endpoint should include blurhash data when cover exists."""
        from app.models import BookCover

        db_session.add(BookCover(
            book_id="book_1",
            thumbnail_url="https://cdn.example.com/book_1/thumb.jpg",
            card_url="https://cdn.example.com/book_1/card.jpg",
            detail_url="https://cdn.example.com/book_1/detail.jpg",
            blurhash="LKO2?U%2Tw=w]~RBVZRi};RPxuwH",
        ))
        db_session.commit()

        resp = client.get("/api/books/book_1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["blurhash"] == "LKO2?U%2Tw=w]~RBVZRi};RPxuwH"
        assert data["detail_cdn"] == "https://cdn.example.com/book_1/detail.jpg"
