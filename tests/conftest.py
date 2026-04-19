"""Shared test fixtures for VenueFlow.

Centralises fixture definitions that were previously duplicated
across ``test_app.py`` and ``test_pipeline.py``.
"""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient

from app import create_app
from app.cache import cache_clear
from app.security import _rate_limits


@pytest.fixture
def client() -> FlaskClient:
    """Create a Flask test client with TESTING mode enabled."""
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset all mutable global state between tests.

    Clears the in-memory cache and rate-limit tracker both before
    and after each test to ensure full isolation.
    """
    cache_clear()
    _rate_limits.clear()
    yield
    cache_clear()
    _rate_limits.clear()
