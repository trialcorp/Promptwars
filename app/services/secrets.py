"""Google Cloud Secret Manager integration."""

from __future__ import annotations

from app.config import Config
from app.services.logging_client import logger


def get_secret(secret_id: str, default: str = "") -> str:
    """Retrieve a secret from Google Cloud Secret Manager."""
    if not Config.PROJECT:
        return default
    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{Config.PROJECT}/secrets/{secret_id}/versions/latest"
        payload = client.access_secret_version(request={"name": name}).payload
        logger.info("Secret '%s' loaded from Secret Manager", secret_id)
        return payload.data.decode("UTF-8")
    except Exception as exc:
        logger.warning("Secret '%s' unavailable: %s", secret_id, exc)
        return default
