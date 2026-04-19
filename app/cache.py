"""In-memory response cache with TTL and LRU eviction."""

from __future__ import annotations

import hashlib
import threading
import time
from typing import Any, Optional

from app.config import Config

_store: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def cache_key(text: str) -> str:
    """Generate deterministic cache key via SHA-256."""
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:16]


def cache_get(key: str) -> Optional[dict[str, Any]]:
    """Retrieve cached result if present and not expired."""
    with _lock:
        entry = _store.get(key)
        if entry and time.time() - entry["ts"] < Config.CACHE_TTL_SECONDS:
            return entry["data"]
        if entry:
            del _store[key]
    return None


def cache_set(key: str, data: dict[str, Any]) -> None:
    """Store result with LRU eviction when full."""
    with _lock:
        if len(_store) >= Config.MAX_CACHE_ENTRIES:
            oldest = min(_store, key=lambda k: _store[k]["ts"])
            del _store[oldest]
        _store[key] = {"data": data, "ts": time.time()}


def cache_clear() -> None:
    """Clear all cached entries."""
    with _lock:
        _store.clear()
