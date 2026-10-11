import time
import json
import asyncio
import logging
from typing import Any, Dict, Optional, Tuple

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from app.config.settings import settings

logger = logging.getLogger("QinxiaoMusic.Cache")

MAX_MEMORY_CACHE_ITEMS = 2000


class CacheManager:
    """Async cache manager supporting Redis with an automatic in-memory TTL fallback."""

    def __init__(self):
        self._redis = None
        self._use_redis: bool = False
        self._memory_cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def init_cache(self) -> None:
        if settings.USE_REDIS and settings.REDIS_URL and aioredis is not None:
            try:
                self._redis = aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._redis.ping()
                self._use_redis = True
                logger.info("Connected to Redis cache successfully.")
                return
            except Exception as e:
                logger.warning(f"Redis connection failed ({e}). Falling back to in-memory cache.")
                self._redis = None
                self._use_redis = False
        else:
            logger.info("Using in-memory TTL cache.")

    def _prune_expired_unlocked(self, now: float) -> None:
        expired_keys = [k for k, (_, exp) in self._memory_cache.items() if exp <= now]
        for k in expired_keys:
            self._memory_cache.pop(k, None)

        if len(self._memory_cache) >= MAX_MEMORY_CACHE_ITEMS:
            # Evict oldest expiring entries first
            sorted_keys = sorted(self._memory_cache.items(), key=lambda item: item[1][1])
            for k, _ in sorted_keys[: len(self._memory_cache) - MAX_MEMORY_CACHE_ITEMS + 100]:
                self._memory_cache.pop(k, None)

    async def get(self, key: str) -> Optional[Any]:
        if self._use_redis and self._redis:
            try:
                raw = await self._redis.get(key)
                if raw is not None:
                    return json.loads(raw)
                return None
            except Exception as e:
                logger.debug(f"Redis GET error for key '{key}': {e}")

        now = time.monotonic()
        async with self._lock:
            entry = self._memory_cache.get(key)
            if not entry:
                return None
            val, expires_at = entry
            if now >= expires_at:
                del self._memory_cache[key]
                return None
            return val

    async def set(self, key: str, value: Any, ttl: int = 600) -> None:
        if self._use_redis and self._redis:
            try:
                await self._redis.set(key, json.dumps(value), ex=max(1, ttl))
                return
            except Exception as e:
                logger.debug(f"Redis SET error for key '{key}': {e}")

        now = time.monotonic()
        async with self._lock:
            self._prune_expired_unlocked(now)
            self._memory_cache[key] = (value, now + max(1, ttl))

    async def delete(self, key: str) -> None:
        if self._use_redis and self._redis:
            try:
                await self._redis.delete(key)
            except Exception as e:
                logger.debug(f"Redis DELETE error for key '{key}': {e}")

        async with self._lock:
            self._memory_cache.pop(key, None)

    async def clear(self) -> None:
        if self._use_redis and self._redis:
            try:
                await self._redis.flushdb()
            except Exception as e:
                logger.debug(f"Redis FLUSHDB error: {e}")

        async with self._lock:
            self._memory_cache.clear()

    async def stats(self) -> Dict[str, Any]:
        if self._use_redis and self._redis:
            try:
                dbsize = await self._redis.dbsize()
                return {"backend": "redis", "keys": dbsize}
            except Exception:
                pass

        now = time.monotonic()
        async with self._lock:
            self._prune_expired_unlocked(now)
            return {"backend": "memory", "keys": len(self._memory_cache)}


cache = CacheManager()
