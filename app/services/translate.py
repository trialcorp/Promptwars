"""Google Cloud Translate v3 — language detection and translation.

This module handles ONLY Google Cloud Translate operations.
Gemini-based fallback is handled separately in the pipeline layer.
"""

from __future__ import annotations

from typing import Any

from app.config import Config
from app.constants import DEFAULT_LANGUAGE, LANGUAGE_DETECT_MAX_CHARS
from app.services.logging_client import logger


def _init_translate() -> tuple[Any, str, bool]:
    """Initialize Cloud Translate v3 client.

    Returns:
        A triple of (client, parent_resource_path, is_available).
    """
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
    """Detect the language of ``text`` using Google Cloud Translate v3.

    Args:
        text: The input text (only the first ``LANGUAGE_DETECT_MAX_CHARS``
              characters are sent to the API).

    Returns:
        An ISO 639-1 language code, defaulting to ``"en"`` on failure.
    """
    if not TRANSLATE_AVAILABLE or not _client:
        return DEFAULT_LANGUAGE
    try:
        resp = _client.detect_language(
            request={
                "parent": _parent,
                "content": text[:LANGUAGE_DETECT_MAX_CHARS],
                "mime_type": "text/plain",
            }
        )
        detected: str = resp.languages[0].language_code
        logger.info("Cloud Translate detected: %s", detected)
        return detected
    except Exception as exc:
        logger.warning("Language detection failed: %s", exc)
        return DEFAULT_LANGUAGE


def translate_text(text: str, target_lang: str) -> str:
    """Translate ``text`` into ``target_lang`` using Cloud Translate v3.

    Args:
        text: Source text to translate.
        target_lang: Target ISO 639-1 language code.

    Returns:
        The translated string, or the original ``text`` on failure.
    """
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


def translate_json_values(
    data: dict[str, Any], target_lang: str
) -> dict[str, Any]:
    """Recursively translate all human-facing string values in a dict.

    Skips keys starting with ``_`` (metadata) and preserves non-string
    values.  Uses Google Cloud Translate v3 for each string value.

    Args:
        data: The dictionary whose string values should be translated.
        target_lang: Target ISO 639-1 language code.

    Returns:
        A new dictionary with translated string values.
    """
    if target_lang == DEFAULT_LANGUAGE or not TRANSLATE_AVAILABLE:
        return data

    translated: dict[str, Any] = {}
    for key, value in data.items():
        if key.startswith("_"):
            translated[key] = value
        elif isinstance(value, str) and len(value) > 0:
            translated[key] = translate_text(value, target_lang)
        elif isinstance(value, list):
            translated[key] = [
                translate_text(item, target_lang) if isinstance(item, str)
                else translate_json_values(item, target_lang) if isinstance(item, dict)
                else item
                for item in value
            ]
        elif isinstance(value, dict):
            translated[key] = translate_json_values(value, target_lang)
        else:
            translated[key] = value
    return translated
