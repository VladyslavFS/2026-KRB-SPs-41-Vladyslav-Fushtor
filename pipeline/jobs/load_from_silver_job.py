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


def to_dt(x) -> datetime | None:
    if x is None or pd.isna(x):
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


def safe_int(x) -> int | None:
    if pd.isna(x) or x is None:
        return None
    return int(x)


def safe_float(x) -> float | None:
    if pd.isna(x) or x is None:
        return None
    return float(x)


def safe_str(x) -> str | None:
    if pd.isna(x) or x is None:
        return None
    return str(x)


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
            # Read parquet into pandas DataFrame
            df = con.execute(f"SELECT * FROM read_parquet('{local_path}')").df()
            con.close()

        rows: list[dict] = []
        for _, r in df.iterrows():
            row = {
                "id": safe_str(r["id"]),
                "time": to_dt(r["time"]),
                "updated": to_dt(r["updated"]),
                "latitude": safe_float(r["latitude"]),
                "longitude": safe_float(r["longitude"]),
                "depth": safe_float(r["depth"]),
                "mag": safe_float(r["mag"]),
                "mag_type": safe_str(r["mag_type"]),
                "place": safe_str(r["place"]),
                "event_type": safe_str(r["event_type"]),
                "status": safe_str(r["status"]),
                "net": safe_str(r["net"]),
                "url": safe_str(r["url"]),
                "detail": safe_str(r["detail"]),
                "tsunami": safe_int(r["tsunami"]),
                "country": safe_str(r.get("country")),
                # New fields (handling pd.NA safely)
                "alert": safe_str(r["alert"]),
                "sig": safe_int(r["sig"]),
                "felt": safe_int(r["felt"]),
                "mmi": safe_float(r["mmi"]),
                "nst": safe_int(r["nst"]),
                "gap": safe_float(r["gap"]),
                "mag_error": safe_float(r["mag_error"]),
                # Window
                "source_window_start": to_dt(r["source_window_start"]),
                "source_window_end": to_dt(r["source_window_end"]),
            }
            rows.append(row)

        return self.repo.upsert_earthquakes(rows)
    