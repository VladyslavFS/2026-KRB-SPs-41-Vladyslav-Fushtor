"""
Date utilities — replaces duplicated _daterange() in 3 job files.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterator


def daterange(start: date, end_exclusive: date) -> Iterator[date]:
    """
    Yields every date from start up to (but not including) end_exclusive.

    Example:
        list(daterange(date(2026, 1, 1), date(2026, 1, 4)))
        # -> [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]
    """
    cur = start
    while cur < end_exclusive:
        yield cur
        cur += timedelta(days=1)
