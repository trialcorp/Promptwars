"""VenueFlow — Flask application factory.

AI-powered crowd intelligence platform for live sporting events.
Built by volunteer.media for PromptWars Virtual 2026.
"""

from __future__ import annotations

from flask import Flask, jsonify
from flask import Response as FlaskResponse

from app.config import Config
from app.security import apply_security_headers
from app.services.logging_client import logger


def create_app() -> Flask:
    """Create and configure the Flask application."""
    flask_app = Flask(__name__, template_folder="../templates")
    flask_app.config["MAX_CONTENT_LENGTH"] = Config.MAX_REQUEST_SIZE

    # Security middleware
    flask_app.after_request(apply_security_headers)

    # Error handlers — return consistent JSON responses
    @flask_app.errorhandler(404)
    def not_found(error: Exception) -> tuple[FlaskResponse, int]:
        return jsonify({"error": "Resource not found."}), 404

    @flask_app.errorhandler(405)
    def method_not_allowed(error: Exception) -> tuple[FlaskResponse, int]:
        return jsonify({"error": "Method not allowed."}), 405

    @flask_app.errorhandler(500)
    def internal_error(error: Exception) -> tuple[FlaskResponse, int]:
        logger.error("Internal server error: %s", error)
        return jsonify({"error": "Internal server error."}), 500

    # Register route blueprint
    from app.routes import api
    flask_app.register_blueprint(api)

    logger.info("VenueFlow application created")
    return flask_app
