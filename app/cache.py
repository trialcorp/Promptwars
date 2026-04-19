"""In-memory response cache with TTL and O(1) LRU eviction.

Uses ``OrderedDict`` so that eviction of the oldest entry is a
constant-time ``popitem(last=False)`` instead of a linear scan.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from typing import Any

from app.config import Config

_store: OrderedDict[str, dict[str, Any]] = OrderedDict()
_lock = threading.Lock()


def cache_key(text: str) -> str:
    """Generate a deterministic, case-insensitive cache key via SHA-256.

    Leading/trailing whitespace and casing are normalized so that
    ``"Hello"`` and ``"  hello  "`` produce the same key.
    """
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:16]


def cache_get(key: str) -> dict[str, Any] | None:
    """Retrieve a cached result if present and not expired.

    Expired entries are evicted on access (lazy invalidation).

    Args:
        key: The cache key returned by ``cache_key()``.

    Returns:
        The cached data dict, or ``None`` on miss / expiry.
    """
    with _lock:
        entry = _store.get(key)
        if entry and time.time() - entry["ts"] < Config.CACHE_TTL_SECONDS:
            _store.move_to_end(key)  # Mark as recently used
            return entry["data"]
        if entry:
            del _store[key]
    return None


def cache_set(key: str, data: dict[str, Any]) -> None:
    """Store a result, evicting the oldest entry if the cache is full.

    Eviction is O(1) via ``OrderedDict.popitem(last=False)``.
    """
    with _lock:
        if key in _store:
            _store.move_to_end(key)
        elif len(_store) >= Config.MAX_CACHE_ENTRIES:
            _store.popitem(last=False)  # O(1) — evict oldest
        _store[key] = {"data": data, "ts": time.time()}


def cache_clear() -> None:
    """Clear all cached entries."""
    with _lock:
        _store.clear()
