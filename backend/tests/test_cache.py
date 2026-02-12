"""Tests for Redis cache service with mocked Redis."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services import cache

# Save references to the real functions before any autouse fixtures run patching
_real_cache_get = cache.cache_get
_real_cache_set = cache.cache_set
_real_cache_delete = cache.cache_delete
_real_blacklist_add = cache.blacklist_add
_real_blacklist_check = cache.blacklist_check
_real_redis_ping = cache.redis_ping


@pytest.fixture()
def mock_redis_client():
    """Create a mock Redis client for direct cache module testing."""
    client = AsyncMock()
    client.ping.return_value = True
    client.get.return_value = None
    client.set.return_value = True
    client.delete.return_value = 1
    client.aclose.return_value = None
    return client


class TestCacheGetSet:
    """Test cache_get and cache_set with mocked Redis."""

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, mock_redis_client):
        """Test setting and getting a value from cache."""
        test_data = {"key": "value", "count": 42}
        mock_redis_client.get.return_value = json.dumps(test_data)

        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            await _real_cache_set("test:key", test_data, ttl=3600)
            mock_redis_client.set.assert_called_once_with(
                "test:key", json.dumps(test_data), ex=3600
            )
            result = await _real_cache_get("test:key")
            assert result == test_data

    @pytest.mark.asyncio
    async def test_cache_get_miss(self, mock_redis_client):
        """Test cache miss returns None."""
        mock_redis_client.get.return_value = None

        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            result = await _real_cache_get("nonexistent:key")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_without_ttl(self, mock_redis_client):
        """Test setting a value without TTL (permanent)."""
        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            await _real_cache_set("perm:key", {"data": "permanent"})
            mock_redis_client.set.assert_called_once_with(
                "perm:key", json.dumps({"data": "permanent"})
            )

    @pytest.mark.asyncio
    async def test_cache_get_graceful_on_error(self, mock_redis_client):
        """Test cache_get returns None when Redis errors."""
        mock_redis_client.get.side_effect = ConnectionError("Redis down")

        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            result = await _real_cache_get("test:key")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_graceful_on_error(self, mock_redis_client):
        """Test cache_set silently handles Redis errors."""
        mock_redis_client.set.side_effect = ConnectionError("Redis down")

        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            # Should not raise
            await _real_cache_set("test:key", {"data": "value"}, ttl=60)


class TestCacheDelete:
    """Test cache_delete with mocked Redis."""

    @pytest.mark.asyncio
    async def test_cache_delete(self, mock_redis_client):
        """Test deleting a key from cache."""
        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            await _real_cache_delete("test:key")
            mock_redis_client.delete.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_cache_delete_graceful_on_error(self, mock_redis_client):
        """Test cache_delete silently handles Redis errors."""
        mock_redis_client.delete.side_effect = ConnectionError("Redis down")

        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            await _real_cache_delete("test:key")


class TestBlacklist:
    """Test token blacklist operations with mocked Redis."""

    @pytest.mark.asyncio
    async def test_blacklist_add(self, mock_redis_client):
        """Test adding a JTI to the blacklist."""
        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            await _real_blacklist_add("test-jti-123", ttl=900)
            mock_redis_client.set.assert_called_once_with(
                "blacklist:test-jti-123", "1", ex=900
            )

    @pytest.mark.asyncio
    async def test_blacklist_check_found(self, mock_redis_client):
        """Test checking a blacklisted JTI returns True."""
        mock_redis_client.get.return_value = "1"

        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            result = await _real_blacklist_check("test-jti-123")
            assert result is True

    @pytest.mark.asyncio
    async def test_blacklist_check_not_found(self, mock_redis_client):
        """Test checking a non-blacklisted JTI returns False."""
        mock_redis_client.get.return_value = None

        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            result = await _real_blacklist_check("test-jti-456")
            assert result is False

    @pytest.mark.asyncio
    async def test_blacklist_check_graceful_on_error(self, mock_redis_client):
        """Test blacklist_check returns None when Redis is unavailable."""
        mock_redis_client.get.side_effect = ConnectionError("Redis down")

        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            result = await _real_blacklist_check("test-jti-789")
            assert result is None

    @pytest.mark.asyncio
    async def test_blacklist_add_graceful_on_error(self, mock_redis_client):
        """Test blacklist_add silently handles Redis errors."""
        mock_redis_client.set.side_effect = ConnectionError("Redis down")

        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            await _real_blacklist_add("test-jti-000", ttl=900)


class TestRedisPing:
    """Test Redis health check."""

    @pytest.mark.asyncio
    async def test_redis_ping_success(self, mock_redis_client):
        """Test ping returns True when Redis is healthy."""
        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            result = await _real_redis_ping()
            assert result is True

    @pytest.mark.asyncio
    async def test_redis_ping_failure(self, mock_redis_client):
        """Test ping returns False when Redis is down."""
        mock_redis_client.ping.side_effect = ConnectionError("Redis down")

        with patch.object(cache, "get_redis", return_value=mock_redis_client):
            result = await _real_redis_ping()
            assert result is False


class TestHealthEndpoint:
    """Test health endpoint includes Redis status."""

    def test_health_includes_redis_status(self, client):
        """Test that /health returns Redis status."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "dependencies" in data
        assert "redis" in data["dependencies"]
        assert data["dependencies"]["redis"] in ("connected", "unavailable")
        assert data["status"] in ("healthy", "unhealthy")
