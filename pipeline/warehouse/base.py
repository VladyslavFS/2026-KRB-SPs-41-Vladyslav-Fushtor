"""
Warehouse Repository interfaces.

Pattern: Repository (separates data access from business logic).
Concrete implementations live in event_repository.py and dq_repository.py.
PostgresRepository (pg.py) implements both for backward compatibility.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import pandas as pd

from pipeline.dq.thresholds import DQStats


class IEventRepository(ABC):
    """Contract for earthquake event persistence."""

    @abstractmethod
    @contextmanager
    def connection(self):
        """Context manager: yields a DB connection, commits on success, rollbacks on error."""
        ...
        yield  # required for contextmanager + abstractmethod

    @abstractmethod
    def upsert_earthquakes(self, rows: list[dict]) -> int:
        """UPSERT rows into ODS. Returns count of input rows."""
        ...

    @abstractmethod
    def insert_df(
        self,
        *,
        conn,
        table: str,
        df: pd.DataFrame,
        on_conflict: str | None = None,
    ) -> None:
        """Generic bulk insert from a pandas DataFrame."""
        ...


class IDQRepository(ABC):
    """Contract for Data Quality results persistence."""

    @abstractmethod
    @contextmanager
    def connection(self):
        """Context manager: yields a DB connection, commits on success, rollbacks on error."""
        ...
        yield

    @abstractmethod
    def fetch_dq_stats(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        conn=None,
    ) -> DQStats:
        """Query ODS and return aggregated DQ statistics for a time window."""
        ...

    @abstractmethod
    def create_dq_run(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        status: str,
        total_rows: int,
        issues_count: int,
        conn=None,
    ) -> int:
        """Insert a new dq_run record and return its run_id."""
        ...

    @abstractmethod
    def insert_dq_issues(
        self,
        *,
        run_id: int,
        issues: list[dict],
        conn=None,
    ) -> None:
        """Bulk-insert DQ issues for a run."""
        ...

    @abstractmethod
    def insert_dq_metrics(
        self,
        *,
        run_id: int,
        metrics: dict[str, float],
        conn=None,
    ) -> None:
        """Bulk-insert DQ metrics for a run."""
        ...
