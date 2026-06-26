"""
Redis caching service for the news aggregator.
Provides fast access to frequently requested data.
"""
import json
import logging
from typing import Optional, Any
from datetime import timedelta, timezone

from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory fallback cache when Redis is unavailable
_memory_cache: dict[str, tuple[Any, float]] = {}
_memory_ttl: float = 86400.0  # 24 hours default (in-memory fallback)

DIGEST_CACHE_TTL = 43200  # 12 hours for digest content

try:
    import redis.asyncio as aioredis
    _redis_client: Optional[aioredis.Redis] = None

    def _get_client() -> Optional[aioredis.Redis]:
        global _redis_client
        if _redis_client is None:
            try:
                _redis_client = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2,
                )
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory cache: {e}")
                return None
        return _redis_client
except ImportError:
    logger.info("redis package not available, using in-memory cache")
    _redis_client = None

    def _get_client():
        return None


async def cache_get(key: str) -> Optional[str]:
    """Get a value from cache (Redis or in-memory fallback)."""
    client = _get_client()
    if client:
        try:
            return await client.get(key)
        except Exception as e:
            logger.debug(f"Redis get failed: {e}")

    # In-memory fallback
    if key in _memory_cache:
        value, expiry = _memory_cache[key]
        import time
        if time.time() < expiry:
            return value
        del _memory_cache[key]
    return None


async def cache_set(key: str, value: str, ttl_seconds: int = 300) -> None:
    """Set a value in cache with TTL."""
    client = _get_client()
    if client:
        try:
            await client.setex(key, ttl_seconds, value)
            return
        except Exception as e:
            logger.debug(f"Redis set failed: {e}")

    # In-memory fallback
    import time
    _memory_cache[key] = (value, time.time() + ttl_seconds)


async def cache_delete(key: str) -> None:
    """Delete a key from cache."""
    client = _get_client()
    if client:
        try:
            await client.delete(key)
            return
        except Exception as e:
            logger.debug(f"Redis delete failed: {e}")

    _memory_cache.pop(key, None)


def _digest_cache_key(user_id: str, digest_type: str = "morning_briefing") -> str:
    return f"digest:{user_id}:{digest_type}"


async def get_cached_digest(user_id: str, digest_type: str = "morning_briefing") -> Optional[str]:
    """Get cached digest content for a user."""
    key = _digest_cache_key(user_id, digest_type)
    return await cache_get(key)


async def set_cached_digest(user_id: str, content: str, digest_type: str = "morning_briefing") -> None:
    """Cache digest content for a user (TTL: 12 hours)."""
    key = _digest_cache_key(user_id, digest_type)
    await cache_set(key, content, ttl_seconds=DIGEST_CACHE_TTL)


async def invalidate_digest_cache(user_id: str) -> None:
    """Invalidate all cached digests for a user."""
    for dtype in ["morning_briefing", "on_demand"]:
        await cache_delete(_digest_cache_key(user_id, dtype))