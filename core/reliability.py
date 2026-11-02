"""
Reliability, Retries, and Concurrency Governance for AI IncidentOps (Layer 14).
Provides exponential backoff decorators, concurrency synchronization, and idempotency checks.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Dict, Set

logger = logging.getLogger("ai_incidentops.reliability")


class IdempotencyRegistry:
    """Thread-safe idempotency registry to prevent duplicate alert processing."""

    def __init__(self, ttl_seconds: int = 3600):
        self._processed_keys: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self.ttl = ttl_seconds

    async def check_and_set(self, key: str) -> bool:
        """Returns True if the key is new (allowed); False if already processed."""
        async with self._lock:
            now = time.time()
            # Clean expired keys
            self._processed_keys = {k: exp for k, exp in self._processed_keys.items() if exp > now}

            if key in self._processed_keys:
                return False  # Duplicate

            self._processed_keys[key] = now + self.ttl
            return True


idempotency_guard = IdempotencyRegistry()


def retry_with_backoff(max_retries: int = 3, initial_delay: float = 0.5, backoff_factor: float = 2.0):
    """Decorator to retry asynchronous functions with exponential backoff."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_err = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    if attempt == max_retries:
                        logger.error(f"[Retry] Function '{func.__name__}' failed after {max_retries} attempts: {str(e)}")
                        raise
                    logger.warning(f"[Retry] Attempt {attempt} failed: {str(e)}. Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
            raise last_err
        return wrapper
    return decorator
