"""Crowd report data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CrowdReport:
    """Represents a single crowd report from an attendee."""

    input_text: str
    detected_language: str = "en"
    report_type: str = "GENERAL"
    severity: str = "INFO"
    title: str = ""
    location_in_venue: str = ""
    crowd_density: str = "UNKNOWN"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_firestore_dict(self) -> dict:
        """Convert to a dict suitable for Firestore storage."""
        return {
            "input_preview": self.input_text[:200],
            "detected_language": self.detected_language,
            "report_type": self.report_type,
            "severity": self.severity,
            "title": self.title,
            "location_in_venue": self.location_in_venue,
            "crowd_density": self.crowd_density,
            "timestamp": self.timestamp,
        }
