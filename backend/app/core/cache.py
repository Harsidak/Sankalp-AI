"""
In-memory cache with a Redis-compatible interface.

For the hackathon, this uses a simple dict with TTL support.
Swap to Redis by changing the implementation — the interface stays the same.
"""

import time
from typing import Any, Optional


class InMemoryCache:
    """
    Simple in-memory key-value cache with TTL support.
    Thread-safe for single-process async applications.

    Drop-in replacement interface for Redis:
    - get(key) -> value or None
    - set(key, value, ttl) -> None
    - delete(key) -> None
    - exists(key) -> bool
    - incr(key) -> int
    """

    def __init__(self):
        self._store: dict[str, tuple[Any, Optional[float]]] = {}

    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired and clean it up if so."""
        if key not in self._store:
            return True
        _, expires_at = self._store[key]
        if expires_at is not None and time.time() > expires_at:
            del self._store[key]
            return True
        return False

    async def get(self, key: str) -> Optional[Any]:
        """Get a value by key. Returns None if not found or expired."""
        if self._is_expired(key):
            return None
        value, _ = self._store[key]
        return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a key-value pair with optional TTL (in seconds).
        If ttl is None, the value never expires.
        """
        expires_at = (time.time() + ttl) if ttl else None
        self._store[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        return not self._is_expired(key)

    async def incr(self, key: str) -> int:
        """
        Increment a numeric value by 1. Creates the key with value 1 if it doesn't exist.
        Preserves the existing TTL.
        """
        if self._is_expired(key):
            await self.set(key, 1)
            return 1
        value, expires_at = self._store[key]
        new_value = int(value) + 1
        self._store[key] = (new_value, expires_at)
        return new_value

    async def clear(self) -> None:
        """Clear all cached data."""
        self._store.clear()

    def cleanup_expired(self) -> int:
        """Remove all expired keys. Returns number of keys removed."""
        now = time.time()
        expired_keys = [
            key for key, (_, expires_at) in self._store.items()
            if expires_at is not None and now > expires_at
        ]
        for key in expired_keys:
            del self._store[key]
        return len(expired_keys)


# Module-level singleton
_cache: Optional[InMemoryCache] = None


def get_cache() -> InMemoryCache:
    """Get the cache singleton."""
    global _cache
    if _cache is None:
        _cache = InMemoryCache()
    return _cache
