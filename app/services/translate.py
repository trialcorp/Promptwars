"""Google Cloud Translate v3 — language detection and translation.

This module handles ONLY Google Cloud Translate operations.
Gemini-based fallback is handled separately in the pipeline layer.
"""

from __future__ import annotations

from typing import Any, Optional

from app.config import Config
from app.services.logging_client import logger


def _init_translate() -> tuple[Any, str, bool]:
    """Initialize Cloud Translate v3 client."""
    if not Config.PROJECT:
        return None, "", False
    try:
        from google.cloud import translate_v3 as translate

        client = translate.TranslationServiceClient()
        parent = f"projects/{Config.PROJECT}/locations/global"
        logger.info("Cloud Translate v3 initialized")
        return client, parent, True
    except Exception as exc:
        logger.warning("Cloud Translate unavailable: %s", exc)
        return None, "", False


_client, _parent, TRANSLATE_AVAILABLE = _init_translate()


def detect_language(text: str) -> str:
    """Detect language using Google Cloud Translate v3."""
    if not TRANSLATE_AVAILABLE or not _client:
        return "en"
    try:
        resp = _client.detect_language(
            request={"parent": _parent, "content": text[:500], "mime_type": "text/plain"}
        )
        detected = resp.languages[0].language_code
        logger.info("Cloud Translate detected: %s", detected)
        return detected
    except Exception as exc:
        logger.warning("Language detection failed: %s", exc)
        return "en"


def translate_text(text: str, target_lang: str) -> str:
    """Translate text using Google Cloud Translate v3."""
    if not TRANSLATE_AVAILABLE or not _client:
        return text
    try:
        resp = _client.translate_text(
            request={
                "parent": _parent,
                "contents": [text],
                "target_language_code": target_lang,
                "mime_type": "text/plain",
            }
        )
        return resp.translations[0].translated_text
    except Exception as exc:
        logger.error("Translation error: %s", exc)
        return text


def translate_json_values(data: dict, target_lang: str) -> dict:
    """Recursively translate all string values in a dict.

    Skips keys starting with '_' (metadata) and preserves non-string values.
    Uses Google Cloud Translate v3 for each string value.
    """
    if target_lang == "en" or not TRANSLATE_AVAILABLE:
        return data

    translated: dict = {}
    for key, value in data.items():
        if key.startswith("_"):
            translated[key] = value
        elif isinstance(value, str) and len(value) > 0:
            translated[key] = translate_text(value, target_lang)
        elif isinstance(value, list):
            translated[key] = [
                translate_text(item, target_lang) if isinstance(item, str) else
                translate_json_values(item, target_lang) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, dict):
            translated[key] = translate_json_values(value, target_lang)
        else:
            translated[key] = value
    return translated
