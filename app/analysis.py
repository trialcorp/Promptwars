"""Gemini AI analysis for crowd report classification and venue intelligence.

Sends user-submitted crowd reports to Gemini with a structured JSON schema
and retries on transient failures or malformed responses.
"""

from __future__ import annotations

import json
import time
from typing import Any

from google.genai import types as genai_types

from app.config import Config
from app.constants import (
    AI_MAX_OUTPUT_TOKENS,
    AI_RETRY_DELAY_SEC,
    AI_TEMPERATURE,
    MAX_AI_RETRIES,
)
from app.exceptions import AIAnalysisError
from app.services.gemini import gemini_client
from app.services.logging_client import logger


SYSTEM_PROMPT: str = """You are VenueFlow — an AI-powered crowd intelligence assistant
for large-scale sporting events and stadiums. Your job is to analyze crowd reports
from attendees and generate structured, actionable venue intelligence.

JSON SCHEMA:
{
  "report_type": "CROWD | FOOD | PARKING | WEATHER | SAFETY | FACILITY | NAVIGATION | GENERAL",
  "severity": "CRITICAL | HIGH | MODERATE | LOW | INFO",
  "title": "string — short summary of the report",
  "summary": "string — 2-3 sentence overview of the situation",
  "location_in_venue": "string — identified location (gate, section, stand, food court, parking lot, etc.)",
  "crowd_density": "VERY_HIGH | HIGH | MODERATE | LOW | UNKNOWN",
  "key_insights": ["list of 3-5 key observations extracted"],
  "recommended_actions": ["list of 3-5 specific actions for the attendee"],
  "wait_time_estimate": "string — estimated wait time if applicable, else 'N/A'",
  "alternative_suggestions": ["list of 2-3 less crowded alternatives nearby"],
  "safety_alert": {
    "is_safety_concern": true/false,
    "details": "string — safety details if applicable"
  },
  "event_phase_relevance": "PRE_EVENT | DURING_EVENT | HALFTIME | POST_EVENT | ANY",
  "confidence": "HIGH | MEDIUM | LOW"
}

RULES:
- Always respond ONLY with valid JSON, no markdown, no extra text.
- If input is vague, still provide best guidance with caveats.
- Think about Indian sporting events context (IPL cricket, ISL football, PKL kabaddi).
- Common venue locations: Gate A-F, Sections 1-50, North/South/East/West Stand,
  Food Court 1-4, Parking Lot A-D, VIP Lounge, General Stand, Gallery.
- Always suggest alternatives to reduce crowd at reported locations.
- For safety concerns (stampede risk, medical, fire, weather), set severity to HIGH or CRITICAL.
- Emergency contacts for India: Police: 100, Ambulance: 108, Fire: 101.
- Be practical and concise — attendees are checking on their phones.
"""


def _extract_json(raw: str) -> str:
    """Extract the outermost JSON object from a potentially messy AI response.

    Finds the first ``{`` and last ``}`` to handle cases where the model
    wraps its response in markdown fences or preamble text.
    """
    start_idx = raw.find("{")
    end_idx = raw.rfind("}")
    if start_idx != -1 and end_idx != -1:
        return raw[start_idx: end_idx + 1]
    return raw


def analyze_report(user_input: str) -> dict[str, Any]:
    """Analyze a crowd report using Gemini AI with retry logic.

    Args:
        user_input: The crowd report text (in English).

    Returns:
        Structured analysis dict with an ``_meta`` key containing
        processing metadata.

    Raises:
        AIAnalysisError: If all retry attempts are exhausted.
    """
    if gemini_client is None:
        logger.error("Gemini client not initialized")
        return {"error": "AI analysis service is unavailable. Please check configuration."}

    start = time.time()
    last_error = ""

    for attempt in range(MAX_AI_RETRIES + 1):
        try:
            response = gemini_client.models.generate_content(
                model=Config.MODEL_ID,
                config=genai_types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=AI_TEMPERATURE,
                    max_output_tokens=AI_MAX_OUTPUT_TOKENS,
                ),
                contents=user_input,
            )
            raw_text = response.text.strip()
            raw = _extract_json(raw_text)
            result: dict[str, Any] = json.loads(raw)

            elapsed = round(time.time() - start, 2)
            result["_meta"] = {
                "processing_time_sec": elapsed,
                "model": Config.MODEL_ID,
                "attempts": attempt + 1,
            }
            logger.info("Report analyzed in %ss (attempt %d)", elapsed, attempt + 1)
            return result

        except json.JSONDecodeError as exc:
            last_error = f"JSON parse error: {exc}"
            logger.warning(
                "Attempt %d — %s | Raw response (truncated): %.200s",
                attempt + 1,
                last_error,
                raw_text if "raw_text" in dir() else "<unavailable>",
            )
        except Exception as exc:
            last_error = str(exc)
            logger.warning("Attempt %d — AI error: %s", attempt + 1, last_error)

        if attempt < MAX_AI_RETRIES:
            time.sleep(AI_RETRY_DELAY_SEC)

    return {"error": f"AI analysis failed after {MAX_AI_RETRIES + 1} attempts. {last_error}"}
