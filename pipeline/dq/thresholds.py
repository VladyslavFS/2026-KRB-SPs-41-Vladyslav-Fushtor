"""
DQ Value Objects — DQThresholds, DQIssue, DQStats.
These are pure data containers with no business logic.

Pattern: Value Object (frozen dataclasses — immutable, equality by value).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DQThresholds:
    """
    Configurable Data Quality thresholds.
    Defaults represent production SLAs.
    Pass a custom instance to DataQualityJob for environment-specific overrides.
    """
    warn_ingest_lag_min: float = 180.0      # 3 h
    error_ingest_lag_min: float = 720.0     # 12 h

    warn_pct_missing_geo: float = 0.01      # 1 %
    error_pct_missing_geo: float = 0.10     # 10 %

    warn_pct_missing_mag: float = 0.20      # 20 %
    error_pct_missing_mag: float = 0.60     # 60 %

    max_valid_mag: float = 10.0
    min_valid_mag: float = -2.0


@dataclass(frozen=True)
class DQIssue:
    """A single data quality finding."""
    issue_type: str
    severity: str           # "ERROR" | "WARN"
    message: str
    sample_ids: list | None = None


@dataclass
class DQStats:
    """
    Statistics collected from the ODS layer for a given time window.
    Produced by IDQRepository.fetch_dq_stats() and consumed by IDQCheck.check().
    """
    total_rows: int
    pct_missing_geo: float
    pct_missing_mag: float
    pct_with_alert: float
    pct_with_mmi: float
    pct_missing_sig: float
    val_min_mag: float | None
    val_max_mag: float | None
    val_min_sig: float | None
    avg_update_delay_min: float
    avg_ingest_lag_min: float
    max_ingest_lag_min: float
    max_event_time: datetime | None
