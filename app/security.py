"""Security: headers, rate limiting, and input sanitization.

The rate limiter uses an in-memory sliding-window counter with periodic
cleanup to prevent unbounded memory growth from unique IP addresses.
"""

from __future__ import annotations

import time
from typing import Any

from flask import Response as FlaskResponse

from app.config import Config
from app.constants import (
    MAX_TRACKED_IPS,
    RATE_LIMIT_CLEANUP_INTERVAL_SEC,
    RATE_LIMIT_WINDOW_SEC,
)

# ===================================================================
# Security Headers
# ===================================================================
SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(self)",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://maps.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self' https://maps.googleapis.com"
    ),
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


def apply_security_headers(response: FlaskResponse) -> FlaskResponse:
    """Apply security headers to every HTTP response."""
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


# ===================================================================
# Rate Limiter (sliding-window with periodic cleanup)
# ===================================================================
_rate_limits: dict[str, list[float]] = {}
_last_cleanup: float = 0.0


def _purge_stale_entries(now: float) -> None:
    """Remove IP entries whose timestamps are all outside the window.

    Also enforces ``MAX_TRACKED_IPS`` by dropping the oldest half
    of entries when the cap is exceeded.
    """
    stale_keys = [
        ip for ip, timestamps in _rate_limits.items()
        if not timestamps or all(now - t >= RATE_LIMIT_WINDOW_SEC for t in timestamps)
    ]
    for ip in stale_keys:
        del _rate_limits[ip]

    # Hard cap — if still too many, drop oldest entries
    if len(_rate_limits) > MAX_TRACKED_IPS:
        sorted_ips = sorted(
            _rate_limits,
            key=lambda ip: max(_rate_limits[ip]) if _rate_limits[ip] else 0.0,
        )
        for ip in sorted_ips[: len(sorted_ips) // 2]:
            del _rate_limits[ip]


def check_rate_limit(ip: str) -> bool:
    """Return ``True`` if the IP is within the allowed request rate.

    Performs periodic cleanup of stale entries to bound memory usage.

    Args:
        ip: Client IP address (or ``X-Forwarded-For`` header value).
    """
    global _last_cleanup  # noqa: PLW0603
    now = time.time()

    # Periodic full cleanup
    if now - _last_cleanup > RATE_LIMIT_CLEANUP_INTERVAL_SEC:
        _purge_stale_entries(now)
        _last_cleanup = now

    timestamps = _rate_limits.setdefault(ip, [])
    _rate_limits[ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SEC]

    if len(_rate_limits[ip]) >= Config.MAX_REQUESTS_PER_MINUTE:
        return False

    _rate_limits[ip].append(now)
    return True


# ===================================================================
# Input Sanitization
# ===================================================================
def sanitize_input(text: Any) -> str:
    """Remove null bytes, control characters, and normalize whitespace.

    Args:
        text: Raw user input (may be ``None`` or a non-string type).

    Returns:
        A sanitized, whitespace-normalized string.
    """
    if not isinstance(text, str):
        return ""
    text = text.replace("\x00", "")
    text = "".join(ch for ch in text if ch in ("\n", "\t") or ch.isprintable())
    text = " ".join(text.split())
    return text.strip()
