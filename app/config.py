"""Centralized application configuration."""

from __future__ import annotations

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """All settings loaded from environment variables with sensible defaults."""

    # Google Cloud
    PROJECT: str = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    REGION: str = os.environ.get("REGION", "asia-south1")
    IS_CLOUD: bool = bool(os.environ.get("K_SERVICE", ""))

    # AI Model
    MODEL_ID: str = os.environ.get("MODEL_ID", "gemini-2.5-flash")

    # Input Limits
    MAX_INPUT_LENGTH: int = 5000
    MAX_REQUEST_SIZE: int = 1 * 1024 * 1024  # 1 MB

    # Caching
    CACHE_TTL_SECONDS: int = 120  # 2 min — shorter for real-time data
    MAX_CACHE_ENTRIES: int = 200

    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 30  # Higher for crowd-sourced app

    # Storage
    GCS_BUCKET: str = os.environ.get("GCS_BUCKET", "")
    GCS_REPORT_PREFIX: str = "reports/"
    FIRESTORE_COLLECTION: str = "crowd_reports"
    FIRESTORE_ZONES_COLLECTION: str = "venue_zones"

    # Google Maps
    MAPS_API_KEY: str = os.environ.get("MAPS_API_KEY", "")

    # Server
    PORT: int = int(os.environ.get("PORT", 8080))

    # Supported Languages
    SUPPORTED_LANGUAGES: dict[str, str] = {
        "en": "English",
        "hi": "हिन्दी",
        "te": "తెలుగు",
        "ta": "தமிழ்",
        "kn": "ಕನ್ನಡ",
        "mr": "मराठी",
    }
