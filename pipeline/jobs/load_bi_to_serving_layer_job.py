from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta, datetime, timezone
from typing import Iterable

import duckdb
import pandas as pd

from pipeline.storage.storage import ObjectStorage
from pipeline.warehouse.pg import PostgresRepository


def _daterange(start: date, end_exclusive: date) -> Iterable[date]:
    cur = start
    while cur < end_exclusive:
        yield cur
        cur += timedelta(days=1)


@dataclass(frozen=True)
class LoadBIToServingLayerJob:
    """
    Syncs Gold Parquet from S3 to Postgres BI tables (Serving Layer).
    Strategy: Delete-Insert for specific days.
    """
    repo: PostgresRepository
    storage: ObjectStorage
    bucket: str

    def run(self, *, days: int) -> None:
        if days <= 0:
            raise ValueError("days must be > 0")

        today = datetime.now(timezone.utc).date()
        start_day = today - timedelta(days=days - 1)
        end_day_excl = today + timedelta(days=1)

        tables = ["event_feed", "top_events_daily", "catalog_health_daily"]

        with self.repo.connection() as conn:
            for table in tables:
                print(f"Syncing table: bi.{table}...")
                for d in _daterange(start_day, end_day_excl):
                    self._sync_partition(conn, table, d)

    def _sync_partition(self, conn, table: str, d: date):
        dt_str = d.isoformat()
        prefix = f"gold/bi/{table}/dt={dt_str}/"
        
        keys = self.storage.list_keys(prefix=prefix)
        if not keys:
            # No data in S3 -> clear DB day to match
            self._delete_day(conn, table, d)
            return

        # Pick latest key (part-YYYYMMddTHHmmssZ.parquet sorts correctly)
        latest_key = sorted(keys)[-1]

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "data.parquet")
            self.storage.download_file(key=latest_key, local_path=local_path)

            with duckdb.connect() as con:
                try:
                     df = con.execute(f"SELECT * FROM read_parquet('{local_path}')").df()
                except Exception:
                     # Handle empty or corrupted parquet gracefully
                     df = pd.DataFrame()

        if df.empty:
            self._delete_day(conn, table, d)
            return

        # Transactional Replace
        self._delete_day(conn, table, d)
        on_conflict = None
        if table == "event_feed":
            on_conflict = "ON CONFLICT (event_id) DO NOTHING"
        elif table == "top_events_daily":
            on_conflict = "ON CONFLICT (day, rank) DO NOTHING"
        elif table == "catalog_health_daily":
            on_conflict = "ON CONFLICT (day) DO NOTHING"
            
        self.repo.insert_df(conn=conn, table=f"bi.{table}", df=df, on_conflict=on_conflict)
        print(f"  -> Loaded {d}: {len(df)} rows (source: {latest_key})")

    def _delete_day(self, conn, table: str, d: date):
        date_col = "(time AT TIME ZONE 'UTC')::date" if table == "event_feed" else "day"
        sql = f"DELETE FROM bi.{table} WHERE {date_col} = %s"
        with conn.cursor() as cur:
            cur.execute(sql, (d,))