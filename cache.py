import hashlib
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

from cachetools import TTLCache

# In-memory cache with 24h TTL, max 1000 entries
_memory_cache: TTLCache = TTLCache(maxsize=1000, ttl=86400)


class CacheLayer:
    """Two-tier cache: Redis (if available) with in-memory fallback."""

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        if self._redis is not None:
            return self._redis
        if not HAS_REDIS:
            return None
        import os
        redis_url = os.getenv("REDIS_URL", "")
        if not redis_url:
            return None
        try:
            self._redis = await aioredis.from_url(redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("Redis connected")
            return self._redis
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}, using in-memory cache")
            return None

    def _cache_key(self, resume_id: str, job_description: str = "") -> str:
        """Generate a cache key from resume content hash and job description."""
        if job_description:
            jd_hash = hashlib.md5(job_description.encode()).hexdigest()[:8]
            return f"ra:{resume_id}:{jd_hash}"
        return f"ra:{resume_id}"

    async def get(self, resume_id: str, job_description: str = "") -> Optional[dict]:
        key = self._cache_key(resume_id, job_description)
        # Try Redis first
        redis_conn = await self._get_redis()
        if redis_conn:
            try:
                data = await redis_conn.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        # Fallback to memory
        return _memory_cache.get(key)

    async def set(self, resume_id: str, data: dict, job_description: str = "") -> None:
        key = self._cache_key(resume_id, job_description)
        # Try Redis first
        redis_conn = await self._get_redis()
        if redis_conn:
            try:
                await redis_conn.setex(key, 86400, json.dumps(data, ensure_ascii=False))
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
        # Always set in memory too
        _memory_cache[key] = data


# Singleton
cache = CacheLayer()
