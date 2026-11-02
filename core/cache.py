"""
Caching Subsystem for AI IncidentOps (Layer 10).
Provides caching for service registry metadata and runbooks.
Supports Redis when reachable, with automatic in-memory TTL fallback.
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional
from core.config import settings


class CacheClient:
    """Thread-safe caching client with Redis and in-memory fallback."""

    def __init__(self):
        self._memory_cache: dict[str, tuple[Any, float]] = {}
        self._redis = None
        self._redis_available = False

        # Attempt Redis connection if configured
        try:
            import redis
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=1.0)
            self._redis.ping()
            self._redis_available = True
        except Exception:
            self._redis_available = False

    def get(self, key: str) -> Optional[Any]:
        if self._redis_available and self._redis:
            try:
                val = self._redis.get(key)
                return json.loads(val) if val else None
            except Exception:
                self._redis_available = False

        # Memory cache fallback
        if key in self._memory_cache:
            val, expiry = self._memory_cache[key]
            if time.time() < expiry:
                return val
            del self._memory_cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        if self._redis_available and self._redis:
            try:
                self._redis.setex(key, ttl_seconds, json.dumps(value))
                return
            except Exception:
                self._redis_available = False

        # Memory cache fallback
        expiry = time.time() + ttl_seconds
        self._memory_cache[key] = (value, expiry)

    def invalidate(self, key: str) -> None:
        if self._redis_available and self._redis:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        self._memory_cache.pop(key, None)


cache = CacheClient()
