"""Google Cloud Firestore — crowd reports and venue zone storage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.config import Config
from app.services.logging_client import logger


def _init_firestore() -> tuple[Any, bool]:
    """Initialize Firestore client."""
    if not Config.PROJECT:
        return None, False
    try:
        from google.cloud import firestore

        client = firestore.Client(project=Config.PROJECT)
        logger.info("Cloud Firestore initialized")
        return client, True
    except Exception as exc:
        logger.warning("Firestore unavailable: %s", exc)
        return None, False


_client, FIRESTORE_AVAILABLE = _init_firestore()


def store_report(report_data: dict[str, Any]) -> Optional[str]:
    """Store a crowd report in Firestore. Returns document ID."""
    if not FIRESTORE_AVAILABLE or not _client:
        return None
    try:
        doc_data = {
            **report_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _, doc_ref = _client.collection(Config.FIRESTORE_COLLECTION).add(doc_data)
        logger.info("Report stored: %s", doc_ref.id)
        return doc_ref.id
    except Exception as exc:
        logger.error("Firestore write error: %s", exc)
        return None


def get_recent_reports(limit: int = 20) -> list[dict[str, Any]]:
    """Retrieve recent crowd reports ordered by timestamp."""
    if not FIRESTORE_AVAILABLE or not _client:
        return []
    try:
        from google.cloud import firestore

        docs = (
            _client.collection(Config.FIRESTORE_COLLECTION)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as exc:
        logger.error("Firestore read error: %s", exc)
        return []


def get_zone_stats() -> list[dict[str, Any]]:
    """Retrieve venue zone statistics."""
    if not FIRESTORE_AVAILABLE or not _client:
        return []
    try:
        docs = _client.collection(Config.FIRESTORE_ZONES_COLLECTION).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as exc:
        logger.error("Firestore zones error: %s", exc)
        return []


def update_zone_density(zone_id: str, density: str, report_count: int) -> None:
    """Update crowd density for a venue zone."""
    if not FIRESTORE_AVAILABLE or not _client:
        return
    try:
        _client.collection(Config.FIRESTORE_ZONES_COLLECTION).document(zone_id).set(
            {
                "density": density,
                "report_count": report_count,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            merge=True,
        )
    except Exception as exc:
        logger.error("Zone update error: %s", exc)
