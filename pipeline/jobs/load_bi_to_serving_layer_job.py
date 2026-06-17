from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import duckdb
import pandas as pd

from pipeline.protocols.job import BaseJob
from pipeline.storage.storage import ObjectStorage
from pipeline.utils.date_utils import daterange
from pipeline.warehouse.base import IEventRepository


@dataclass(frozen=True)
class LoadBIToServingLayerJob(BaseJob):
    """
    Syncs Gold Parquet from S3 to Postgres BI tables (Serving Layer).
    Strategy: Delete-Insert for specific days.

    Pattern:
      - BaseJob (Template Method).
      - IEventRepository (Repository).
      - ObjectStorage (Strategy).
      - daterange from shared utils (DRY).
    """
    repo: IEventRepository
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
                for d in daterange(start_day, end_day_excl):
                    self._sync_partition(conn, table, d)

    def _sync_partition(self, conn, table: str, d: date):
        dt_str = d.isoformat()
        prefix = f"gold/bi/{table}/dt={dt_str}/"

        keys = self.storage.list_keys(prefix=prefix)
        if not keys:
            self._delete_day(conn, table, d)
            return

        latest_key = sorted(keys)[-1]

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "data.parquet")
            self.storage.download_file(key=latest_key, local_path=local_path)

            with duckdb.connect() as con:
                try:
                    df = con.execute(f"SELECT * FROM read_parquet('{local_path}')").df()
                except Exception:
                    df = pd.DataFrame()

        if df.empty:
            self._delete_day(conn, table, d)
            return

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

    def _execute(self, **kwargs):
        return self.run(**kwargs)