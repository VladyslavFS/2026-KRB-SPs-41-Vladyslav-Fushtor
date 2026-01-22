from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import datetime

import duckdb
import pandas as pd
from dateutil import parser as dtparser

from pipeline.storage.storage import ObjectStorage
from pipeline.warehouse.pg import PostgresRepository


def to_dt(x) -> datetime:
    if x is None:
        return None

    # pandas Timestamp
    if isinstance(x, pd.Timestamp):
        return x.to_pydatetime()

    # already datetime
    if isinstance(x, datetime):
        return x

    # bytes -> str
    if isinstance(x, (bytes, bytearray)):
        x = x.decode("utf-8")

    return dtparser.isoparse(str(x))


@dataclass(frozen=True)
class LoadFromSilverJob:
    storage: ObjectStorage
    repo: PostgresRepository

    def run(self, *, silver_key: str) -> int:
        """
        Downloads parquet from storage, reads it, converts to rows, upserts to Postgres.
        Returns number of rows passed to upsert.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "silver.parquet")
            self.storage.download_file(key=silver_key, local_path=local_path)

            con = duckdb.connect()
            df = con.execute(f"SELECT * FROM read_parquet('{local_path}')").df()
            con.close()

        rows: list[dict] = []
        for _, r in df.iterrows():
            row = {
                "id": str(r["id"]),
                "time": to_dt(r["time"]),
                "updated": to_dt(r["updated"]),
                "latitude": None if r["latitude"] is None else float(r["latitude"]),
                "longitude": None if r["longitude"] is None else float(r["longitude"]),
                "depth": None if r["depth"] is None else float(r["depth"]),
                "mag": r["mag"],
                "mag_type": r["mag_type"],
                "place": r["place"],
                "event_type": r["event_type"],
                "status": r["status"],
                "net": r["net"],
                "url": r["url"],
                "detail": r["detail"],
                "tsunami": r["tsunami"],
                "source_window_start": to_dt(r["source_window_start"]),
                "source_window_end": to_dt(r["source_window_end"]),
            }
            rows.append(row)

        return self.repo.upsert_earthquakes(rows)
