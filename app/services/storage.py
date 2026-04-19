"""Google Cloud Storage — report archival."""

from __future__ import annotations

import json
from typing import Any, Optional

from app.config import Config
from app.services.logging_client import logger


def _init_storage() -> tuple[Any, bool]:
    """Initialize Cloud Storage bucket."""
    if not Config.PROJECT:
        return None, False
    try:
        from google.cloud import storage

        client = storage.Client(project=Config.PROJECT)
        bucket_name = Config.GCS_BUCKET or f"{Config.PROJECT}-venueflow-reports"
        try:
            bucket = client.get_bucket(bucket_name)
        except Exception:
            bucket = client.create_bucket(bucket_name, location=Config.REGION)
            logger.info("Created GCS bucket: %s", bucket_name)
        logger.info("Cloud Storage initialized: %s", bucket_name)
        return bucket, True
    except Exception as exc:
        logger.warning("Cloud Storage unavailable: %s", exc)
        return None, False


_bucket, GCS_AVAILABLE = _init_storage()


def store_report_gcs(report_id: str, data: dict[str, Any]) -> Optional[str]:
    """Store a full report as JSON in Cloud Storage."""
    if not GCS_AVAILABLE or not _bucket:
        return None
    try:
        blob_name = f"{Config.GCS_REPORT_PREFIX}{report_id}.json"
        blob = _bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(data, indent=2, ensure_ascii=False),
            content_type="application/json",
        )
        logger.info("Report archived in GCS: %s", blob_name)
        return blob_name
    except Exception as exc:
        logger.error("GCS write error: %s", exc)
        return None
