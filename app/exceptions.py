"""Custom exception hierarchy for VenueFlow.

Provides fine-grained error classification so that callers can
distinguish between transient infrastructure failures, user input
errors, and AI processing issues — instead of catching bare
``Exception`` everywhere.
"""

from __future__ import annotations


class VenueFlowError(Exception):
    """Base exception for all VenueFlow application errors."""


class AIAnalysisError(VenueFlowError):
    """Gemini AI analysis failed after all retry attempts.

    Attributes:
        attempts: Number of attempts made before giving up.
        last_error: Description of the final failure.
    """

    def __init__(self, attempts: int, last_error: str) -> None:
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"AI analysis failed after {attempts} attempts. {last_error}"
        )


class TranslationError(VenueFlowError):
    """Google Cloud Translate operation failed."""


class StorageError(VenueFlowError):
    """Cloud Storage or Firestore persistence operation failed."""


class RateLimitExceededError(VenueFlowError):
    """Client has exceeded the per-minute request rate limit.

    Attributes:
        client_ip: The IP address that was rate-limited.
    """

    def __init__(self, client_ip: str) -> None:
        self.client_ip = client_ip
        super().__init__(f"Rate limit exceeded for {client_ip}")


class InputValidationError(VenueFlowError):
    """User input failed validation checks (empty, too long, etc.)."""
