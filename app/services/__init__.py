"""Google Cloud services registry.

Services:
    - Vertex AI + Gemini 2.5 Flash — AI analysis
    - Cloud Translate v3 — multilingual I/O
    - Cloud Firestore — real-time crowd reports
    - Cloud Storage — report archival
    - Cloud Logging — production monitoring
    - Cloud Secret Manager — secure config
    - Cloud Run — deployment (runtime)
"""

from app.services.logging_client import logger
from app.services.secrets import get_secret
from app.services.gemini import gemini_client
from app.services.translate import (
    detect_language,
    translate_text,
    translate_json_values,
    TRANSLATE_AVAILABLE,
)
from app.services.firestore_client import (
    store_report,
    get_recent_reports,
    get_zone_stats,
    update_zone_density,
    FIRESTORE_AVAILABLE,
)
from app.services.storage import store_report_gcs, GCS_AVAILABLE

__all__ = [
    "logger",
    "get_secret",
    "gemini_client",
    "detect_language",
    "translate_text",
    "translate_json_values",
    "TRANSLATE_AVAILABLE",
    "store_report",
    "get_recent_reports",
    "get_zone_stats",
    "update_zone_density",
    "FIRESTORE_AVAILABLE",
    "store_report_gcs",
    "GCS_AVAILABLE",
]
