"""Redis cache service with connection pooling and graceful fallback."""

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger("bookswipe")

_pool: redis.ConnectionPool | None = None
_client: redis.Redis | None = None


def _get_pool() -> redis.ConnectionPool:
    """Get or create the Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
    return _pool


def get_redis() -> redis.Redis:
    """Get a Redis client backed by the shared connection pool."""
    global _client
    if _client is None:
        _client = redis.Redis(connection_pool=_get_pool())
    return _client


async def redis_ping() -> bool:
    """Check if Redis is reachable. Returns False on any error."""
    try:
        return await get_redis().ping()
    except Exception:
        return False


async def cache_get(key: str) -> Any | None:
    """Get a value from Redis cache. Returns None if unavailable or missing."""
    try:
        raw = await get_redis().get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.warning("Redis cache GET failed for key=%s, skipping cache", key)
        return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    """Set a value in Redis cache. Silently skips on error."""
    try:
        raw = json.dumps(value)
        if ttl is not None:
            await get_redis().set(key, raw, ex=ttl)
        else:
            await get_redis().set(key, raw)
    except Exception:
        logger.warning("Redis cache SET failed for key=%s, skipping cache", key)


async def cache_delete(key: str) -> None:
    """Delete a key from Redis cache. Silently skips on error."""
    try:
        await get_redis().delete(key)
    except Exception:
        logger.warning("Redis cache DELETE failed for key=%s", key)


# --- Token blacklist operations ---

async def blacklist_add(jti: str, ttl: int) -> None:
    """Add a JTI to the token blacklist SET with TTL matching token expiry."""
    try:
        await get_redis().set(f"blacklist:{jti}", "1", ex=ttl)
    except Exception:
        logger.warning("Redis blacklist ADD failed for jti=%s, skipping", jti)


async def blacklist_check(jti: str) -> bool | None:
    """Check if a JTI is blacklisted. Returns None if Redis is unavailable."""
    try:
        result = await get_redis().get(f"blacklist:{jti}")
        return result is not None
    except Exception:
        logger.warning("Redis blacklist CHECK failed for jti=%s", jti)
        return None


async def close_redis() -> None:
    """Close the Redis connection pool on shutdown."""
    global _client, _pool
    if _client is not None:
        await _client.aclose()
        _client = None
    if _pool is not None:
        await _pool.aclose()
        _pool = None
