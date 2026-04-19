"""Domain enums for VenueFlow — type-safe string constants.

Using ``StrEnum`` so values serialize naturally to JSON and compare
equal to plain strings (``Severity.HIGH == "HIGH"`` is ``True``).
Requires Python 3.11+.
"""

from __future__ import annotations

from enum import StrEnum


class ReportType(StrEnum):
    """Classification of a crowd report."""

    CROWD = "CROWD"
    FOOD = "FOOD"
    PARKING = "PARKING"
    WEATHER = "WEATHER"
    SAFETY = "SAFETY"
    FACILITY = "FACILITY"
    NAVIGATION = "NAVIGATION"
    GENERAL = "GENERAL"


class Severity(StrEnum):
    """Impact severity of a crowd report."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    INFO = "INFO"


class CrowdDensity(StrEnum):
    """Crowd density level at a venue zone."""

    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class EventPhase(StrEnum):
    """Phase of the sporting event a report is relevant to."""

    PRE_EVENT = "PRE_EVENT"
    DURING_EVENT = "DURING_EVENT"
    HALFTIME = "HALFTIME"
    POST_EVENT = "POST_EVENT"
    ANY = "ANY"


class Confidence(StrEnum):
    """AI confidence level in the analysis result."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
