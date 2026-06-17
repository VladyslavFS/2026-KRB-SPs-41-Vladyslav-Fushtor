"""
TypeCoercer — safe type conversions for DataFrame rows coming from Parquet/DuckDB.
Replaces module-level helper functions that were in load_from_silver_job.py.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
from dateutil import parser as dtparser


class TypeCoercer:
    """
    Static helpers for coercing loosely-typed values (from Parquet/DuckDB)
    to strict Python types. Returns None on null / non-parseable input.

    Pattern: Utility class (no state, all @staticmethod).
    """

    @staticmethod
    def to_dt(x) -> datetime | None:
        """Coerce to timezone-aware datetime. Returns None on null input."""
        if x is None:
            return None
        try:
            if pd.isna(x):
                return None
        except (TypeError, ValueError):
            pass

        if isinstance(x, pd.Timestamp):
            return x.to_pydatetime()
        if isinstance(x, datetime):
            return x
        if isinstance(x, (bytes, bytearray)):
            x = x.decode("utf-8")
        return dtparser.isoparse(str(x))

    @staticmethod
    def safe_int(x) -> int | None:
        """Coerce to int. Returns None on null."""
        try:
            if pd.isna(x) or x is None:
                return None
        except (TypeError, ValueError):
            pass
        return int(x)

    @staticmethod
    def safe_float(x) -> float | None:
        """Coerce to float. Returns None on null."""
        try:
            if pd.isna(x) or x is None:
                return None
        except (TypeError, ValueError):
            pass
        return float(x)

    @staticmethod
    def safe_str(x) -> str | None:
        """Coerce to str. Returns None on null."""
        try:
            if pd.isna(x) or x is None:
                return None
        except (TypeError, ValueError):
            pass
        return str(x)
