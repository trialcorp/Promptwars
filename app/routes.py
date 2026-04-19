"""Flask route definitions for VenueFlow.

This module handles ONLY HTTP request/response logic.
Business logic is delegated to the pipeline module.
"""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, render_template, request, jsonify
from flask import Response as FlaskResponse

from app.config import Config
from app.security import check_rate_limit, sanitize_input
from app.pipeline import process_report
from app.services.logging_client import logger
from app.services.translate import translate_text, TRANSLATE_AVAILABLE
from app.services.firestore_client import get_recent_reports, get_zone_stats, FIRESTORE_AVAILABLE
from app.services.storage import GCS_AVAILABLE
from app.services.gemini import gemini_client

api = Blueprint("api", __name__)


# ===================================================================
# Pages
# ===================================================================
@api.route("/")
def index() -> str:
    """Serve the main UI."""
    return render_template("index.html", maps_api_key=Config.MAPS_API_KEY)


# ===================================================================
# Core: Submit Crowd Report
# ===================================================================
@api.route("/report", methods=["POST"])
def submit_report() -> tuple[FlaskResponse, int] | FlaskResponse:
    """Accept a crowd report → process through AI pipeline → return guidance.

    Response is returned in the SAME language as the input.
    """
    client_ip: str = request.headers.get("X-Forwarded-For", request.remote_addr)
    if not check_rate_limit(client_ip):
        logger.warning("Rate limit exceeded: %s", client_ip)
        return jsonify({"error": "Too many requests. Please wait a moment."}), 429

    data: dict = request.get_json(silent=True) or {}
    user_input: str = sanitize_input(data.get("input", ""))

    if not user_input:
        return jsonify({"error": "Please describe what you're seeing at the venue."}), 400
    if len(user_input) > Config.MAX_INPUT_LENGTH:
        return jsonify({"error": f"Input too long. Max {Config.MAX_INPUT_LENGTH} characters."}), 400

    result, is_cached = process_report(user_input)

    if "error" in result and not is_cached:
        return jsonify(result), 503

    return jsonify(result)


# ===================================================================
# Translation
# ===================================================================
@api.route("/translate", methods=["POST"])
def translate_endpoint() -> tuple[FlaskResponse, int] | FlaskResponse:
    """Translate text using Google Cloud Translate v3."""
    data: dict = request.get_json(silent=True) or {}
    text: str = sanitize_input(data.get("text", ""))
    target: str = data.get("target", "hi")

    if not text:
        return jsonify({"error": "No text provided."}), 400

    translated = translate_text(text, target)
    return jsonify({"translated": translated, "target_language": target})


# ===================================================================
# Live Feed
# ===================================================================
@api.route("/feed", methods=["GET"])
def live_feed() -> FlaskResponse:
    """Retrieve recent crowd reports — the live venue pulse."""
    limit = min(int(request.args.get("limit", 20)), 50)
    reports = get_recent_reports(limit)
    return jsonify({"reports": reports, "count": len(reports)})


# ===================================================================
# Zone Stats
# ===================================================================
@api.route("/zones", methods=["GET"])
def zones() -> FlaskResponse:
    """Retrieve current crowd density by venue zone."""
    stats = get_zone_stats()
    return jsonify({"zones": stats, "count": len(stats)})


# ===================================================================
# Health Check
# ===================================================================
@api.route("/health")
def health() -> FlaskResponse:
    """Health check — reports status of all integrated Google Cloud services."""
    return jsonify({
        "status": "healthy",
        "app": "VenueFlow by volunteer.media",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": Config.MODEL_ID,
        "services": {
            "vertex_ai": bool(Config.PROJECT),
            "gemini": gemini_client is not None,
            "cloud_translate": TRANSLATE_AVAILABLE,
            "cloud_firestore": FIRESTORE_AVAILABLE,
            "cloud_storage": GCS_AVAILABLE,
            "cloud_logging": Config.IS_CLOUD,
            "secret_manager": bool(Config.PROJECT),
        },
    })
