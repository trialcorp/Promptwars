"""Report processing pipeline — orchestrates the analysis workflow.

Separates business logic from HTTP routing for better maintainability.
Pipeline: detect language → translate → analyze → translate back → persist.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.config import Config
from app.analysis import analyze_report
from app.models.report import CrowdReport
from app.services.logging_client import logger
from app.services.translate import (
    detect_language,
    translate_text,
    translate_json_values,
    TRANSLATE_AVAILABLE,
)
from app.services.firestore_client import store_report, FIRESTORE_AVAILABLE
from app.services.storage import store_report_gcs, GCS_AVAILABLE
from app.cache import cache_key, cache_get, cache_set


def process_report(user_input: str) -> tuple[dict[str, Any], bool]:
    """Process a crowd report through the full analysis pipeline.

    Returns:
        A tuple of (result_dict, is_cached).
        result_dict contains the AI analysis or an error.
    """
    # Step 1: Detect input language
    detected_lang = detect_language(user_input)
    logger.info("Processing report | language: %s", detected_lang)

    # Step 2: Check cache
    key = cache_key(user_input)
    cached = cache_get(key)
    if cached:
        logger.info("Cache hit: %s", key)
        cached.setdefault("_meta", {})["cached"] = True
        return cached, True

    # Step 3: Translate to English for analysis (if needed)
    input_for_analysis = user_input
    if detected_lang != "en" and TRANSLATE_AVAILABLE:
        input_for_analysis = translate_text(user_input, "en")
        logger.info("Translated %s → en for analysis", detected_lang)

    # Step 4: AI analysis (always in English for best accuracy)
    result = analyze_report(input_for_analysis)
    if "error" in result:
        return result, False

    # Step 5: Translate entire response back to user's language
    if detected_lang != "en" and TRANSLATE_AVAILABLE:
        result = translate_json_values(result, detected_lang)
        logger.info("Response translated en → %s", detected_lang)

    # Step 6: Add language metadata
    result.setdefault("_meta", {})["detected_language"] = detected_lang
    result["_meta"]["response_language"] = detected_lang

    # Step 7: Cache the translated result
    cache_set(key, result)

    # Step 8: Persist to Cloud Storage
    report_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + key
    if GCS_AVAILABLE:
        store_report_gcs(report_id, result)

    # Step 9: Store metadata in Firestore
    if FIRESTORE_AVAILABLE:
        report = CrowdReport(
            input_text=user_input,
            detected_language=detected_lang,
            report_type=result.get("report_type", "GENERAL"),
            severity=result.get("severity", "INFO"),
            title=result.get("title", ""),
            location_in_venue=result.get("location_in_venue", ""),
            crowd_density=result.get("crowd_density", "UNKNOWN"),
        )
        store_report(report.to_firestore_dict())

    return result, False
