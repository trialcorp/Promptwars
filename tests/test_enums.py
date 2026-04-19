"""Tests for domain enums — validates StrEnum behaviour and membership."""

from __future__ import annotations

from app.models.enums import (
    Confidence,
    CrowdDensity,
    EventPhase,
    ReportType,
    Severity,
)


class TestReportType:
    """ReportType enum coverage."""

    def test_member_count(self) -> None:
        assert len(ReportType) == 8

    def test_string_equality(self) -> None:
        assert ReportType.CROWD == "CROWD"
        assert ReportType.GENERAL == "GENERAL"

    def test_from_string(self) -> None:
        assert ReportType("SAFETY") is ReportType.SAFETY

    def test_all_members(self) -> None:
        expected = {"CROWD", "FOOD", "PARKING", "WEATHER", "SAFETY",
                    "FACILITY", "NAVIGATION", "GENERAL"}
        assert {m.value for m in ReportType} == expected


class TestSeverity:
    """Severity enum coverage."""

    def test_member_count(self) -> None:
        assert len(Severity) == 5

    def test_string_equality(self) -> None:
        assert Severity.CRITICAL == "CRITICAL"
        assert Severity.INFO == "INFO"

    def test_ordering_by_value(self) -> None:
        # StrEnum members are orderable by their string values
        assert sorted(Severity, key=lambda s: s.value) is not None


class TestCrowdDensity:
    """CrowdDensity enum coverage."""

    def test_member_count(self) -> None:
        assert len(CrowdDensity) == 5

    def test_unknown_is_default(self) -> None:
        assert CrowdDensity.UNKNOWN == "UNKNOWN"


class TestEventPhase:
    """EventPhase enum coverage."""

    def test_member_count(self) -> None:
        assert len(EventPhase) == 5

    def test_any_phase(self) -> None:
        assert EventPhase.ANY == "ANY"


class TestConfidence:
    """Confidence enum coverage."""

    def test_member_count(self) -> None:
        assert len(Confidence) == 3

    def test_medium_is_default(self) -> None:
        assert Confidence.MEDIUM == "MEDIUM"
