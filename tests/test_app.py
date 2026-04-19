"""Comprehensive tests for VenueFlow.

Run: python -m pytest tests/ -v

Fixtures (``client``, ``reset_state``) are defined in ``conftest.py``
and shared across all test modules.
"""

from __future__ import annotations

import json
import time

from app.cache import cache_clear, cache_get, cache_key, cache_set, _store
from app.config import Config
from app.constants import INPUT_PREVIEW_MAX_LENGTH
from app.models.report import CrowdReport
from app.security import sanitize_input


# ===================================================================
# Index Route
# ===================================================================
class TestIndex:
    """Tests for the root HTML page."""

    def test_returns_200(self, client) -> None:
        assert client.get("/").status_code == 200

    def test_serves_html(self, client) -> None:
        assert b"<!DOCTYPE html>" in client.get("/").data

    def test_contains_title(self, client) -> None:
        assert b"VenueFlow" in client.get("/").data

    def test_has_textarea(self, client) -> None:
        assert b"textarea" in client.get("/").data

    def test_has_language_selector(self, client) -> None:
        assert b"lang-select" in client.get("/").data

    def test_has_examples(self, client) -> None:
        assert b"example-chip" in client.get("/").data

    def test_has_tabs(self, client) -> None:
        data = client.get("/").data
        assert b"tab-report" in data
        assert b"tab-feed" in data
        assert b"tab-about" in data

    def test_has_volunteer_media_branding(self, client) -> None:
        assert b"volunteer.media" in client.get("/").data


# ===================================================================
# Health Endpoint
# ===================================================================
class TestHealth:
    """Tests for /health — service readiness and integration status."""

    def test_returns_200(self, client) -> None:
        assert client.get("/health").status_code == 200

    def test_status_healthy(self, client) -> None:
        data = json.loads(client.get("/health").data)
        assert data["status"] == "healthy"

    def test_has_app_name(self, client) -> None:
        data = json.loads(client.get("/health").data)
        assert "VenueFlow" in data["app"]

    def test_has_timestamp(self, client) -> None:
        assert "timestamp" in json.loads(client.get("/health").data)

    def test_has_model(self, client) -> None:
        assert "model" in json.loads(client.get("/health").data)

    def test_lists_vertex_ai(self, client) -> None:
        assert "vertex_ai" in json.loads(client.get("/health").data)["services"]

    def test_lists_gemini(self, client) -> None:
        assert json.loads(client.get("/health").data)["services"]["gemini"] is True

    def test_lists_translate(self, client) -> None:
        assert "cloud_translate" in json.loads(client.get("/health").data)["services"]

    def test_lists_firestore(self, client) -> None:
        assert "cloud_firestore" in json.loads(client.get("/health").data)["services"]

    def test_lists_storage(self, client) -> None:
        assert "cloud_storage" in json.loads(client.get("/health").data)["services"]

    def test_lists_logging(self, client) -> None:
        assert "cloud_logging" in json.loads(client.get("/health").data)["services"]

    def test_lists_secret_manager(self, client) -> None:
        assert "secret_manager" in json.loads(client.get("/health").data)["services"]


# ===================================================================
# Report Endpoint
# ===================================================================
class TestReport:
    """Tests for /report — input validation and response format."""

    def test_empty_input_400(self, client) -> None:
        assert client.post("/report", json={"input": ""}).status_code == 400

    def test_missing_input_400(self, client) -> None:
        assert client.post("/report", json={}).status_code == 400

    def test_whitespace_only_400(self, client) -> None:
        assert client.post("/report", json={"input": "   "}).status_code == 400

    def test_too_long_400(self, client) -> None:
        resp = client.post("/report", json={"input": "A" * 5001})
        assert resp.status_code == 400
        assert "too long" in json.loads(resp.data)["error"].lower()

    def test_returns_json(self, client) -> None:
        resp = client.post("/report", json={"input": "Gate 3 is very crowded"})
        assert resp.content_type == "application/json"

    def test_error_message_for_empty(self, client) -> None:
        resp = client.post("/report", json={"input": ""})
        data = json.loads(resp.data)
        assert "error" in data
        assert "venue" in data["error"].lower() or "describe" in data["error"].lower()


# ===================================================================
# Translate Endpoint
# ===================================================================
class TestTranslate:
    """Tests for /translate — text translation via Cloud Translate v3."""

    def test_empty_text_400(self, client) -> None:
        assert client.post("/translate", json={"text": ""}).status_code == 400

    def test_missing_text_400(self, client) -> None:
        assert client.post("/translate", json={}).status_code == 400

    def test_returns_translated_key(self, client) -> None:
        resp = client.post("/translate", json={"text": "hello", "target": "hi"})
        data = json.loads(resp.data)
        assert "translated" in data
        assert "target_language" in data


# ===================================================================
# Feed Endpoint
# ===================================================================
class TestFeed:
    """Tests for /feed — live crowd pulse retrieval."""

    def test_returns_200(self, client) -> None:
        assert client.get("/feed").status_code == 200

    def test_has_reports_key(self, client) -> None:
        data = json.loads(client.get("/feed").data)
        assert "reports" in data
        assert "count" in data

    def test_limit_param(self, client) -> None:
        data = json.loads(client.get("/feed?limit=5").data)
        assert data["count"] <= 50

    def test_default_limit(self, client) -> None:
        data = json.loads(client.get("/feed").data)
        assert isinstance(data["reports"], list)

    def test_invalid_limit_uses_default(self, client) -> None:
        """Ensure non-numeric limit param doesn't crash the endpoint."""
        resp = client.get("/feed?limit=abc")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "reports" in data


# ===================================================================
# Zones Endpoint
# ===================================================================
class TestZones:
    """Tests for /zones — venue zone density stats."""

    def test_returns_200(self, client) -> None:
        assert client.get("/zones").status_code == 200

    def test_has_zones_key(self, client) -> None:
        data = json.loads(client.get("/zones").data)
        assert "zones" in data
        assert "count" in data


# ===================================================================
# Error Handlers
# ===================================================================
class TestErrorHandlers:
    """Tests for Flask error handlers (404, 405)."""

    def test_404_returns_json(self, client) -> None:
        resp = client.get("/nonexistent-route")
        assert resp.status_code == 404
        assert "error" in json.loads(resp.data)

    def test_405_returns_json(self, client) -> None:
        resp = client.get("/report")
        assert resp.status_code == 405
        assert "error" in json.loads(resp.data)


# ===================================================================
# Security Headers
# ===================================================================
class TestSecurityHeaders:
    """Tests verifying all security headers are applied correctly."""

    def test_xss(self, client) -> None:
        assert client.get("/").headers["X-XSS-Protection"] == "1; mode=block"

    def test_nosniff(self, client) -> None:
        assert client.get("/").headers["X-Content-Type-Options"] == "nosniff"

    def test_frame_deny(self, client) -> None:
        assert client.get("/").headers["X-Frame-Options"] == "DENY"

    def test_referrer(self, client) -> None:
        assert "strict-origin" in client.get("/").headers["Referrer-Policy"]

    def test_csp(self, client) -> None:
        assert "Content-Security-Policy" in client.get("/").headers

    def test_hsts(self, client) -> None:
        assert "Strict-Transport-Security" in client.get("/").headers

    def test_permissions(self, client) -> None:
        assert "Permissions-Policy" in client.get("/").headers

    def test_headers_on_api(self, client) -> None:
        h = client.get("/health").headers
        assert h["X-Frame-Options"] == "DENY"
        assert h["X-Content-Type-Options"] == "nosniff"

    def test_headers_on_error(self, client) -> None:
        assert client.get("/nope").headers["X-Frame-Options"] == "DENY"

    def test_csp_allows_maps(self, client) -> None:
        csp = client.get("/").headers["Content-Security-Policy"]
        assert "maps.googleapis.com" in csp


# ===================================================================
# Input Sanitization
# ===================================================================
class TestSanitize:
    """Tests for input sanitization utility."""

    def test_removes_null(self) -> None:
        assert "\x00" not in sanitize_input("a\x00b")

    def test_strips_whitespace(self) -> None:
        assert sanitize_input("  a   b  ") == "a b"

    def test_none(self) -> None:
        assert sanitize_input(None) == ""

    def test_int(self) -> None:
        assert sanitize_input(42) == ""

    def test_list(self) -> None:
        assert sanitize_input([]) == ""

    def test_normal(self) -> None:
        assert sanitize_input("hello world") == "hello world"

    def test_unicode_hindi(self) -> None:
        assert len(sanitize_input("गेट 3 पे भीड़ है")) > 0

    def test_unicode_telugu(self) -> None:
        assert len(sanitize_input("గేట్ 3 దగ్గర జనం ఎక్కువ")) > 0

    def test_control_chars(self) -> None:
        r = sanitize_input("abc\x01\x02def")
        assert "\x01" not in r and "\x02" not in r


# ===================================================================
# Cache
# ===================================================================
class TestCache:
    """Tests for the in-memory LRU cache."""

    def test_deterministic_key(self) -> None:
        assert cache_key("hello") == cache_key("hello")

    def test_case_insensitive_key(self) -> None:
        assert cache_key("Hello") == cache_key("  hello  ")

    def test_set_get(self) -> None:
        cache_set("k1", {"v": 1})
        assert cache_get("k1") == {"v": 1}

    def test_miss(self) -> None:
        assert cache_get("nope") is None

    def test_expiry(self) -> None:
        _store["old"] = {"data": {}, "ts": time.time() - 600}
        assert cache_get("old") is None

    def test_lru_eviction(self) -> None:
        for i in range(205):
            cache_set(f"k{i}", {"i": i})
        assert len(_store) <= Config.MAX_CACHE_ENTRIES

    def test_clear(self) -> None:
        cache_set("x", {"a": 1})
        cache_clear()
        assert cache_get("x") is None


# ===================================================================
# Rate Limiting
# ===================================================================
class TestRateLimit:
    """Tests for the sliding-window rate limiter."""

    def test_allows_initial(self, client, monkeypatch) -> None:
        monkeypatch.setattr("app.routes.process_report", lambda *a, **kw: ({"success": True}, False))
        assert client.post("/report", json={"input": "test"}).status_code != 429

    def test_blocks_excess(self, client, monkeypatch) -> None:
        monkeypatch.setattr("app.routes.process_report", lambda *a, **kw: ({"success": True}, False))
        codes = [client.post("/report", json={"input": "t"}).status_code for _ in range(35)]
        assert 429 in codes

    def test_429_has_error(self, client, monkeypatch) -> None:
        monkeypatch.setattr("app.routes.process_report", lambda *a, **kw: ({"success": True}, False))
        for _ in range(32):
            resp = client.post("/report", json={"input": "t"})
        if resp.status_code == 429:
            assert "error" in json.loads(resp.data)


# ===================================================================
# CrowdReport Model
# ===================================================================
class TestCrowdReportModel:
    """Tests for the CrowdReport dataclass."""

    def test_default_values(self) -> None:
        report = CrowdReport(input_text="test")
        assert report.detected_language == "en"
        assert report.report_type == "GENERAL"
        assert report.severity == "INFO"

    def test_custom_values(self) -> None:
        report = CrowdReport(
            input_text="gate 3 crowded",
            detected_language="hi",
            report_type="CROWD",
            severity="HIGH",
            location_in_venue="Gate 3",
        )
        assert report.detected_language == "hi"
        assert report.report_type == "CROWD"
        assert report.location_in_venue == "Gate 3"

    def test_to_firestore_dict(self) -> None:
        report = CrowdReport(input_text="test report", severity="MODERATE")
        d = report.to_firestore_dict()
        assert "input_preview" in d
        assert "timestamp" in d
        assert d["severity"] == "MODERATE"

    def test_input_preview_truncated(self) -> None:
        report = CrowdReport(input_text="A" * 500)
        d = report.to_firestore_dict()
        assert len(d["input_preview"]) == INPUT_PREVIEW_MAX_LENGTH


# ===================================================================
# Config
# ===================================================================
class TestConfig:
    """Tests for application configuration values."""

    def test_max_input(self) -> None:
        assert Config.MAX_INPUT_LENGTH == 5000

    def test_cache_ttl(self) -> None:
        assert Config.CACHE_TTL_SECONDS == 120

    def test_max_cache(self) -> None:
        assert Config.MAX_CACHE_ENTRIES == 200

    def test_rate_limit(self) -> None:
        assert Config.MAX_REQUESTS_PER_MINUTE == 30

    def test_port(self) -> None:
        assert Config.PORT == 8080

    def test_supported_languages(self) -> None:
        langs = Config.SUPPORTED_LANGUAGES
        assert "en" in langs
        assert "hi" in langs
        assert "te" in langs
        assert len(langs) == 6
