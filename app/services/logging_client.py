"""Google Cloud Logging initialization."""

from __future__ import annotations

import logging

from app.config import Config


def init_logging() -> logging.Logger:
    """Cloud Logging in production, stdout locally."""
    if Config.IS_CLOUD:
        try:
            from google.cloud import logging as cloud_logging

            cloud_logging.Client().setup_logging()
            _logger = logging.getLogger("venueflow")
            _logger.info("Google Cloud Logging initialized")
            return _logger
        except Exception:
            pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    return logging.getLogger("venueflow")


logger = init_logging()
