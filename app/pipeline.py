"""Report processing pipeline — orchestrates the analysis workflow.

Separates business logic from HTTP routing for better maintainability.
Pipeline: detect language → translate → analyze → translate back → persist.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.analysis import analyze_report
from app.cache import cache_get, cache_key, cache_set
from app.config import Config
from app.models.enums import CrowdDensity, ReportType, Severity
from app.models.report import CrowdReport
from app.services.firestore_client import FIRESTORE_AVAILABLE, store_report
from app.services.logging_client import logger
from app.services.storage import GCS_AVAILABLE, store_report_gcs
from app.services.translate import (
    TRANSLATE_AVAILABLE,
    detect_language,
    translate_json_values,
    translate_text,
)


def process_report(user_input: str, target_lang: str | None = None) -> tuple[dict[str, Any], bool]:
    """Process a crowd report through the full analysis pipeline.

    Steps:
        1. Detect input language
        2. Check cache
        3. Translate to English (if needed)
        4. AI analysis (always in English)
        5. Translate response to target language (provided or detected)
        6. Add language metadata
        7. Cache the result
        8. Persist to Cloud Storage
        9. Store metadata in Firestore

    Args:
        user_input: Raw crowd report text from the user.
        target_lang: Explicitly requested response language (ISO 639-1).

    Returns:
        A tuple of ``(result_dict, is_cached)``.
        ``result_dict`` contains the AI analysis or an error.
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

    # Step 5: Translate response back to user's language (preferring target_lang if provided)
    final_lang = target_lang or detected_lang
    if final_lang != "en" and TRANSLATE_AVAILABLE:
        result = translate_json_values(result, final_lang)
        logger.info("Response translated en → %s", final_lang)

    # Step 6: Add language metadata
    result.setdefault("_meta", {})["detected_language"] = detected_lang
    result["_meta"]["response_language"] = final_lang

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
            report_type=result.get("report_type", ReportType.GENERAL),
            severity=result.get("severity", Severity.INFO),
            title=result.get("title", ""),
            location_in_venue=result.get("location_in_venue", ""),
            crowd_density=result.get("crowd_density", CrowdDensity.UNKNOWN),
        )
        store_report(report.to_firestore_dict())

    return result, False
