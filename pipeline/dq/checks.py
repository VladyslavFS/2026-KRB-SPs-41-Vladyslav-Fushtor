"""
DQ Checks — Chain of Responsibility pattern.

Each IDQCheck is a single, focused rule. DataQualityJob iterates all checks
and collects DQIssue results. New rules = new class, zero changes to existing code.

Pattern: Chain of Responsibility + Open/Closed Principle.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from pipeline.dq.thresholds import DQIssue, DQStats, DQThresholds


class IDQCheck(ABC):
    """Abstract data quality check."""

    @abstractmethod
    def check(self, stats: DQStats, thresholds: DQThresholds) -> list[DQIssue]:
        """Run this check and return any issues found (empty list = pass)."""
        ...


# ── Concrete Checks ────────────────────────────────────────────────────────────

class EmptyWindowCheck(IDQCheck):
    """Flags windows with no events at all."""

    def check(self, stats: DQStats, thresholds: DQThresholds) -> list[DQIssue]:
        if stats.total_rows == 0:
            return [DQIssue(
                issue_type="EMPTY_WINDOW",
                severity="WARN",
                message="No events found in the window.",
            )]
        return []


class MagnitudeSanityCheck(IDQCheck):
    """Validates magnitude is within physically plausible bounds."""

    def check(self, stats: DQStats, thresholds: DQThresholds) -> list[DQIssue]:
        issues: list[DQIssue] = []
        if stats.val_max_mag is not None and stats.val_max_mag > thresholds.max_valid_mag:
            issues.append(DQIssue(
                issue_type="INVALID_MAGNITUDE",
                severity="ERROR",
                message=(
                    f"Found magnitude > {thresholds.max_valid_mag} "
                    f"(max={stats.val_max_mag}). Possible data error."
                ),
            ))
        if stats.val_min_mag is not None and stats.val_min_mag < thresholds.min_valid_mag:
            issues.append(DQIssue(
                issue_type="INVALID_MAGNITUDE",
                severity="WARN",
                message=(
                    f"Found magnitude < {thresholds.min_valid_mag} "
                    f"(min={stats.val_min_mag}). Unusual but possible."
                ),
            ))
        return issues


class SignificanceSanityCheck(IDQCheck):
    """Validates significance (sig) is non-negative."""

    def check(self, stats: DQStats, thresholds: DQThresholds) -> list[DQIssue]:
        if stats.val_min_sig is not None and stats.val_min_sig < 0:
            return [DQIssue(
                issue_type="INVALID_SIGNIFICANCE",
                severity="ERROR",
                message=f"Found negative significance (min={stats.val_min_sig}).",
            )]
        return []


class IngestLagCheck(IDQCheck):
    """Checks average ingest lag against SLA thresholds."""

    def check(self, stats: DQStats, thresholds: DQThresholds) -> list[DQIssue]:
        lag = stats.avg_ingest_lag_min
        if lag >= thresholds.error_ingest_lag_min:
            return [DQIssue(
                issue_type="INGEST_LAG_SLA",
                severity="ERROR",
                message=f"Avg ingest lag: {lag:.1f} min (>= {thresholds.error_ingest_lag_min}).",
            )]
        if lag >= thresholds.warn_ingest_lag_min:
            return [DQIssue(
                issue_type="INGEST_LAG_SLA",
                severity="WARN",
                message=f"Avg ingest lag high: {lag:.1f} min (>= {thresholds.warn_ingest_lag_min}).",
            )]
        return []


class MissingGeoCheck(IDQCheck):
    """Checks percentage of events with missing geo coordinates."""

    def check(self, stats: DQStats, thresholds: DQThresholds) -> list[DQIssue]:
        pct = stats.pct_missing_geo
        if pct >= thresholds.error_pct_missing_geo:
            return [DQIssue(
                issue_type="MISSING_GEO",
                severity="ERROR",
                message=f"Missing geo: {pct*100:.2f}% (>= {thresholds.error_pct_missing_geo*100:.0f}%).",
            )]
        if pct >= thresholds.warn_pct_missing_geo:
            return [DQIssue(
                issue_type="MISSING_GEO",
                severity="WARN",
                message=f"Missing geo: {pct*100:.2f}% (>= {thresholds.warn_pct_missing_geo*100:.0f}%).",
            )]
        return []


class MissingMagCheck(IDQCheck):
    """Checks percentage of events with missing magnitude."""

    def check(self, stats: DQStats, thresholds: DQThresholds) -> list[DQIssue]:
        pct = stats.pct_missing_mag
        if pct >= thresholds.error_pct_missing_mag:
            return [DQIssue(
                issue_type="MISSING_MAG",
                severity="ERROR",
                message=f"Missing mag: {pct*100:.2f}% (>= {thresholds.error_pct_missing_mag*100:.0f}%).",
            )]
        if pct >= thresholds.warn_pct_missing_mag:
            return [DQIssue(
                issue_type="MISSING_MAG",
                severity="WARN",
                message=f"Missing mag: {pct*100:.2f}% (>= {thresholds.warn_pct_missing_mag*100:.0f}%).",
            )]
        return []


# ── Default check suite ────────────────────────────────────────────────────────

DEFAULT_DQ_CHECKS: tuple[IDQCheck, ...] = (
    EmptyWindowCheck(),
    MagnitudeSanityCheck(),
    SignificanceSanityCheck(),
    IngestLagCheck(),
    MissingGeoCheck(),
    MissingMagCheck(),
)
