"""Image processing service for book cover CDN.

Fetches covers from Google Books, generates multiple size variants,
computes blurhash placeholders, and uploads to S3-compatible storage.
"""

from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING

import blurhash
import boto3
import httpx
from botocore.config import Config as BotoConfig
from PIL import Image

from app.config import settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger("bookswipe.image_service")

# Target widths for each size variant (height is proportional)
SIZES: dict[str, int] = {
    "thumbnail": 150,
    "card": 400,
    "detail": 800,
}


def _get_s3_client() -> S3Client:
    """Create a boto3 S3 client using application settings."""
    kwargs: dict = {
        "service_name": "s3",
        "region_name": settings.s3_region,
        "config": BotoConfig(signature_version="s3v4"),
    }
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    if settings.s3_access_key:
        kwargs["aws_access_key_id"] = settings.s3_access_key
        kwargs["aws_secret_access_key"] = settings.s3_secret_key
    return boto3.client(**kwargs)


def _ensure_bucket(client: S3Client) -> None:
    """Create the S3 bucket if it does not already exist."""
    try:
        client.head_bucket(Bucket=settings.s3_bucket)
    except client.exceptions.ClientError:
        client.create_bucket(Bucket=settings.s3_bucket)
        logger.info("Created S3 bucket: %s", settings.s3_bucket)


async def fetch_cover_image(book_id: str) -> bytes | None:
    """Fetch the highest quality cover image from Google Books.

    Tries direct content URLs with decreasing zoom levels, then falls
    back to the volumeInfo imageLinks. Returns raw image bytes or None.
    """
    base = f"https://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1"

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        for zoom in (0, 3, 2, 1):
            url = f"{base}&zoom={zoom}"
            resp = await client.get(url)
            if resp.status_code == 200 and len(resp.content) > 5000:
                return resp.content

        # Fallback to API imageLinks
        vol_resp = await client.get(
            f"https://www.googleapis.com/books/v1/volumes/{book_id}"
        )
        if vol_resp.status_code == 200:
            image_links = vol_resp.json().get("volumeInfo", {}).get("imageLinks", {})
            for key in ("extraLarge", "large", "medium", "small", "thumbnail"):
                img_url = image_links.get(key, "")
                if not img_url:
                    continue
                if img_url.startswith("http://"):
                    img_url = "https://" + img_url[7:]
                img_resp = await client.get(img_url)
                if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                    return img_resp.content

    return None


def resize_image(image_data: bytes, target_width: int) -> bytes:
    """Resize an image to a target width, maintaining aspect ratio.

    Returns JPEG bytes of the resized image.
    """
    img = Image.open(io.BytesIO(image_data))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Only downscale, never upscale
    if img.width > target_width:
        ratio = target_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((target_width, new_height), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    return buffer.getvalue()


def generate_blurhash(image_data: bytes, components_x: int = 4, components_y: int = 3) -> str:
    """Generate a blurhash placeholder string from image bytes."""
    img = Image.open(io.BytesIO(image_data))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    # Downscale for faster hashing
    img = img.resize((32, 32), Image.LANCZOS)
    return blurhash.encode(img, components_x, components_y)


def upload_to_s3(client: S3Client, key: str, data: bytes, content_type: str = "image/jpeg") -> str:
    """Upload bytes to S3 and return the public URL.

    Args:
        client: boto3 S3 client.
        key: Object key in the bucket.
        data: Raw bytes to upload.
        content_type: MIME type for the object.

    Returns:
        Public URL string for the uploaded object.
    """
    client.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
        CacheControl="public, max-age=31536000",
    )
    if settings.s3_public_url:
        return f"{settings.s3_public_url.rstrip('/')}/{key}"
    if settings.s3_endpoint_url:
        return f"{settings.s3_endpoint_url.rstrip('/')}/{settings.s3_bucket}/{key}"
    return f"https://{settings.s3_bucket}.s3.{settings.s3_region}.amazonaws.com/{key}"


async def process_and_upload_cover(book_id: str) -> dict[str, str] | None:
    """Fetch, resize, and upload cover images for a book.

    Returns a dict with keys: thumbnail_url, card_url, detail_url, blurhash.
    Returns None if no cover image is available.
    """
    image_data = await fetch_cover_image(book_id)
    if not image_data:
        logger.warning("No cover image found for book %s", book_id)
        return None

    s3_client = _get_s3_client()
    _ensure_bucket(s3_client)

    urls: dict[str, str] = {}
    for size_name, target_width in SIZES.items():
        resized = resize_image(image_data, target_width)
        key = f"covers/{book_id}/{size_name}.jpg"
        url = upload_to_s3(s3_client, key, resized)
        urls[f"{size_name}_url"] = url

    hash_str = generate_blurhash(image_data)
    urls["blurhash"] = hash_str

    logger.info("Processed and uploaded covers for book %s", book_id)
    return urls
