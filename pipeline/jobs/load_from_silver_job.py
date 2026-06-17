from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import datetime

import duckdb
import pandas as pd

from pipeline.protocols.job import BaseJob
from pipeline.storage.storage import ObjectStorage
from pipeline.utils.type_coerce import TypeCoercer
from pipeline.warehouse.base import IEventRepository


@dataclass(frozen=True)
class LoadFromSilverJob(BaseJob):
    """
    Downloads a Silver Parquet file, converts rows to typed dicts,
    and upserts into the ODS Postgres table.

    Pattern:
      - BaseJob (Template Method).
      - IEventRepository (Repository) — decoupled from concrete Postgres impl.
      - TypeCoercer (Utility class) — replaces scattered module-level helpers.
      - ObjectStorage (Strategy) — injectable storage backend.
    """
    storage: ObjectStorage
    repo: IEventRepository          # ← was: PostgresRepository

    def run(self, *, silver_key: str) -> int:
        """Downloads parquet, converts rows, upserts to ODS. Returns row count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "silver.parquet")
            self.storage.download_file(key=silver_key, local_path=local_path)

            with duckdb.connect() as con:
                df = con.execute(f"SELECT * FROM read_parquet('{local_path}')").df()

        coerce = TypeCoercer  # alias for readability

        rows: list[dict] = []
        for _, r in df.iterrows():
            rows.append({
                "id": coerce.safe_str(r["id"]),
                "time": coerce.to_dt(r["time"]),
                "updated": coerce.to_dt(r["updated"]),
                "latitude": coerce.safe_float(r["latitude"]),
                "longitude": coerce.safe_float(r["longitude"]),
                "depth": coerce.safe_float(r["depth"]),
                "mag": coerce.safe_float(r["mag"]),
                "mag_type": coerce.safe_str(r["mag_type"]),
                "place": coerce.safe_str(r["place"]),
                "event_type": coerce.safe_str(r["event_type"]),
                "status": coerce.safe_str(r["status"]),
                "net": coerce.safe_str(r["net"]),
                "url": coerce.safe_str(r["url"]),
                "detail": coerce.safe_str(r["detail"]),
                "tsunami": coerce.safe_int(r["tsunami"]),
                "country": coerce.safe_str(r.get("country")),
                "risk_class": coerce.safe_str(r.get("risk_class")),
                "alert": coerce.safe_str(r["alert"]),
                "sig": coerce.safe_int(r["sig"]),
                "felt": coerce.safe_int(r["felt"]),
                "mmi": coerce.safe_float(r["mmi"]),
                "nst": coerce.safe_int(r["nst"]),
                "gap": coerce.safe_float(r["gap"]),
                "mag_error": coerce.safe_float(r["mag_error"]),
                "source_window_start": coerce.to_dt(r["source_window_start"]),
                "source_window_end": coerce.to_dt(r["source_window_end"]),
            })

        return self.repo.upsert_earthquakes(rows)

    def _execute(self, **kwargs):
        return self.run(**kwargs)