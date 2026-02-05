from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone

import duckdb
import pandas as pd

from pipeline.storage.storage import ObjectStorage


@dataclass(frozen=True)
class SilverWriteJob:
    storage: ObjectStorage

    def run(
        self,
        *,
        raw_geojson: bytes,
        window_start: datetime,
        window_end: datetime,
    ) -> str:
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)
        if window_end.tzinfo is None:
            window_end = window_end.replace(tzinfo=timezone.utc)

        payload = json.loads(raw_geojson.decode())

        features = payload.get("features", [])

        rows = []
        for f in features:
            props = f.get("properties", {})
            geometry = f.get("geometry", {})
            id = f.get("id")

            if not id:
                continue

            coords = geometry.get("coordinates", [])
            lon = coords[0] if len(coords) > 0 else None
            lat = coords[1] if len(coords) > 1 else None
            depth = coords[2] if len(coords) > 2 else None

            time_ms = props.get("time")
            updated_ms = props.get("updated")
            if time_ms is None or updated_ms is None:
                continue

            time_dt = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc).isoformat()
            updated_dt = datetime.fromtimestamp(updated_ms / 1000, tz=timezone.utc).isoformat()

            row = {
                "id": str(id),
                "time": time_dt,
                "updated": updated_dt,
                "latitude": float(lat) if lat is not None else None,
                "longitude": float(lon) if lon is not None else None,
                "depth": float(depth) if depth is not None else None,
                "mag": props.get("mag"),
                "mag_type": props.get("magType"),
                "place": props.get("place"),
                "event_type": props.get("type"),
                "status": props.get("status"),
                "net": props.get("net"),
                "url": props.get("url"),
                "detail": props.get("detail"),
                "tsunami": props.get("tsunami"),
                # Extended stats
                "alert": props.get("alert"),  # green, yellow, orange, red
                "sig": int(props.get("sig")) if props.get("sig") is not None else None,
                "felt": int(props.get("felt")) if props.get("felt") is not None else None,
                "mmi": float(props.get("mmi")) if props.get("mmi") is not None else None,
                "nst": int(props.get("nst")) if props.get("nst") is not None else None, # Number of stations
                "gap": float(props.get("gap")) if props.get("gap") is not None else None, # Azimuthal gap
                "mag_error": float(props.get("magError")) if props.get("magError") is not None else None,
                # Window
                "source_window_start": window_start,
                "source_window_end": window_end,
            }
            rows.append(row)
        
        # Handle empty case to preserve schema if possible, or just create empty df
        if not rows:
             df = pd.DataFrame(columns=[
                 "id", "time", "updated", "latitude", "longitude", "depth", "mag", "mag_type",
                 "place", "event_type", "status", "net", "url", "detail", "tsunami",
                 "alert", "sig", "felt", "mmi", "nst", "gap", "mag_error",
                 "source_window_start", "source_window_end"
             ])
        else:
            df = pd.DataFrame(rows)

        conn = duckdb.connect()
        conn.register("rows", df)

        conn.execute(
            """
            CREATE OR REPLACE TABLE silver AS
            SELECT *
            FROM (
                SELECT
                    *,
                    row_number() OVER (PARTITION BY id ORDER BY updated DESC) as rn
                FROM rows
            )
            WHERE rn = 1;
            """
        )

        date = window_start.date().isoformat()
        hour = f"{window_start.hour:02d}"
        silver_key = (
            "silver/earthquake/events/"
            f"date={date}/hour={hour}/"
            f"part-{window_start.strftime('%Y%m%dT%H%M%SZ')}.parquet"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "silver.parquet")
            conn.execute(f"COPY silver TO '{local_path}' (FORMAT 'parquet');")
            conn.close()
            self.storage.upload_file(local_path=local_path, key=silver_key, content_type="application/octet-stream")


        return silver_key