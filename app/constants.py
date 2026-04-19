"""Application-wide constants — no magic numbers in business logic.

Every hard-coded value that influences runtime behaviour lives here.
Reviewers and maintainers can find and tune them in one place.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Input Processing
# ---------------------------------------------------------------------------
INPUT_PREVIEW_MAX_LENGTH: int = 200
"""Maximum characters stored as a preview in Firestore."""

# ---------------------------------------------------------------------------
# AI Analysis
# ---------------------------------------------------------------------------
MAX_AI_RETRIES: int = 2
"""Number of additional attempts after the first call fails."""

AI_RETRY_DELAY_SEC: float = 1.0
"""Seconds to wait between AI retry attempts."""

AI_MAX_OUTPUT_TOKENS: int = 2048
"""Token limit for Gemini model responses."""

AI_TEMPERATURE: float = 0.2
"""Sampling temperature — lower = more deterministic."""

# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------
MAX_TRACKED_IPS: int = 10_000
"""Hard cap on tracked IP addresses to prevent memory exhaustion."""

RATE_LIMIT_CLEANUP_INTERVAL_SEC: float = 300.0
"""Seconds between full purges of stale rate-limit entries."""

RATE_LIMIT_WINDOW_SEC: float = 60.0
"""Sliding window duration for counting requests per IP."""

# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------
DEFAULT_FEED_LIMIT: int = 20
"""Default number of reports returned by the live feed endpoint."""

MAX_FEED_LIMIT: int = 50
"""Maximum number of reports a client can request in one feed call."""

# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------
LANGUAGE_DETECT_MAX_CHARS: int = 500
"""Maximum characters sent to the language detection API."""

DEFAULT_LANGUAGE: str = "en"
"""Fallback language when detection is unavailable."""

DEFAULT_TRANSLATE_TARGET: str = "hi"
"""Default target language for the /translate endpoint."""
