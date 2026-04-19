"""Security: headers, rate limiting, and input sanitization."""

from __future__ import annotations

import time
from typing import Any

from flask import Response as FlaskResponse

from app.config import Config

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
# Rate Limiter
# ===================================================================
_rate_limits: dict[str, list[float]] = {}


def check_rate_limit(ip: str) -> bool:
    """Return True if the IP is within the allowed rate."""
    now = time.time()
    timestamps = _rate_limits.setdefault(ip, [])
    _rate_limits[ip] = [t for t in timestamps if now - t < 60]
    if len(_rate_limits[ip]) >= Config.MAX_REQUESTS_PER_MINUTE:
        return False
    _rate_limits[ip].append(now)
    return True


# ===================================================================
# Input Sanitization
# ===================================================================
def sanitize_input(text: Any) -> str:
    """Remove null bytes, control characters, and normalize whitespace."""
    if not isinstance(text, str):
        return ""
    text = text.replace("\x00", "")
    text = "".join(ch for ch in text if ch in ("\n", "\t") or ch.isprintable())
    text = " ".join(text.split())
    return text.strip()
