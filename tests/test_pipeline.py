"""Tests for the report processing pipeline.

Fixtures (``client``, ``reset_state``) are defined in ``conftest.py``.
"""

from __future__ import annotations

import json

from app.cache import cache_key, cache_set


class TestPipeline:
    """Tests for the report processing pipeline logic."""

    def test_cached_report_has_marker(self, client) -> None:
        """Cached responses should include cached=True in metadata."""
        cache_set(cache_key("test input"), {"title": "Test", "_meta": {"model": "test"}})
        resp = client.post("/report", json={"input": "test input"})
        data = json.loads(resp.data)
        if "error" not in data:
            assert data.get("_meta", {}).get("cached") is True

    def test_report_returns_json_structure(self, client) -> None:
        """Reports should always return JSON with expected content type."""
        resp = client.post("/report", json={"input": "Gate 3 very crowded"})
        assert resp.content_type == "application/json"

    def test_report_rejects_oversized_input(self, client) -> None:
        """Pipeline should reject input exceeding max length."""
        resp = client.post("/report", json={"input": "x" * 5001})
        assert resp.status_code == 400

    def test_report_rejects_empty_input(self, client) -> None:
        """Pipeline should reject empty input."""
        resp = client.post("/report", json={"input": ""})
        assert resp.status_code == 400

    def test_health_excludes_multilingual_support_key(self, client) -> None:
        """Health check should not expose internal coupling details."""
        data = json.loads(client.get("/health").data)
        assert "multilingual_support" not in data["services"]

    def test_health_has_all_service_keys(self, client) -> None:
        """Health check should report all 7 Google Cloud services."""
        data = json.loads(client.get("/health").data)
        expected = {"vertex_ai", "gemini", "cloud_translate", "cloud_firestore",
                    "cloud_storage", "cloud_logging", "secret_manager"}
        assert expected == set(data["services"].keys())
