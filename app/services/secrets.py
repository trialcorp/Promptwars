"""Google Cloud Secret Manager integration.

Secrets are fetched lazily and the underlying gRPC client is
reused across calls to avoid expensive re-initialization.
"""

from __future__ import annotations

from typing import Any

from app.config import Config
from app.services.logging_client import logger

# Lazy-initialized client — created once on first use.
_client: Any | None = None


def _get_client() -> Any:
    """Return a cached ``SecretManagerServiceClient`` instance."""
    global _client  # noqa: PLW0603
    if _client is None:
        from google.cloud import secretmanager

        _client = secretmanager.SecretManagerServiceClient()
    return _client


def get_secret(secret_id: str, default: str = "") -> str:
    """Retrieve a secret value from Google Cloud Secret Manager.

    Args:
        secret_id: The secret name (e.g. ``"gemini-api-key"``).
        default: Value returned when the secret is unavailable.

    Returns:
        The secret payload as a UTF-8 string, or ``default`` on failure.
    """
    if not Config.PROJECT:
        return default
    try:
        client = _get_client()
        name = f"projects/{Config.PROJECT}/secrets/{secret_id}/versions/latest"
        payload = client.access_secret_version(request={"name": name}).payload
        logger.info("Secret '%s' loaded from Secret Manager", secret_id)
        return payload.data.decode("UTF-8")
    except Exception as exc:
        logger.warning("Secret '%s' unavailable: %s", secret_id, exc)
        return default
