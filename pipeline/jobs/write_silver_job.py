from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone

import duckdb
import pandas as pd

from pipeline.enrich.composite_enricher import CompositeEnricher
from pipeline.enrich.geo import GeoEnricher
from pipeline.enrich.risk import RiskClassifier
from pipeline.protocols.enricher import IEnricher
from pipeline.protocols.job import BaseJob
from pipeline.storage.storage import ObjectStorage


def _build_default_enricher() -> IEnricher:
    """Factory: default enrichment pipeline (geo → risk)."""
    return CompositeEnricher(GeoEnricher(), RiskClassifier())


@dataclass(frozen=True)
class SilverWriteJob(BaseJob):
    """
    Parses raw GeoJSON, enriches records (geo + risk), deduplicates,
    and writes a Silver Parquet file to object storage.

    Pattern:
      - BaseJob (Template Method) for uniform job interface.
      - IEnricher / CompositeEnricher (Strategy + Composite) — pluggable enrichment.
      - ObjectStorage (Strategy) — injectable storage backend.
    """
    storage: ObjectStorage
    enricher: IEnricher = None          # None → resolved to default in __post_init__

    def __post_init__(self):
        # dataclass(frozen=True) requires object.__setattr__ for post-init mutation
        if self.enricher is None:
            object.__setattr__(self, "enricher", _build_default_enricher())

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
            event_id = f.get("id")

            if not event_id:
                continue

            coords = geometry.get("coordinates", [])
            lon = coords[0] if len(coords) > 0 else None
            lat = coords[1] if len(coords) > 1 else None
            depth = coords[2] if len(coords) > 2 else None

            time_ms = props.get("time")
            updated_ms = props.get("updated")
            if time_ms is None or updated_ms is None:
                continue

            mag = props.get("mag")

            rows.append({
                "id": str(event_id),
                "time": datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc).isoformat(),
                "updated": datetime.fromtimestamp(updated_ms / 1000, tz=timezone.utc).isoformat(),
                "latitude": float(lat) if lat is not None else None,
                "longitude": float(lon) if lon is not None else None,
                "depth": float(depth) if depth is not None else None,
                "mag": mag,
                "mag_type": props.get("magType"),
                "place": props.get("place"),
                "event_type": props.get("type"),
                "status": props.get("status"),
                "net": props.get("net"),
                "url": props.get("url"),
                "detail": props.get("detail"),
                "tsunami": props.get("tsunami"),
                "alert": props.get("alert"),
                "sig": int(props["sig"]) if props.get("sig") is not None else None,
                "felt": int(props["felt"]) if props.get("felt") is not None else None,
                "mmi": float(props["mmi"]) if props.get("mmi") is not None else None,
                "nst": int(props["nst"]) if props.get("nst") is not None else None,
                "gap": float(props["gap"]) if props.get("gap") is not None else None,
                "mag_error": float(props["magError"]) if props.get("magError") is not None else None,
                "source_window_start": window_start,
                "source_window_end": window_end,
            })

        schema_cols = [
            "id", "time", "updated", "latitude", "longitude", "depth", "mag", "mag_type",
            "place", "event_type", "status", "net", "url", "detail", "tsunami",
            "alert", "sig", "felt", "mmi", "nst", "gap", "mag_error",
            "source_window_start", "source_window_end",
        ]
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=schema_cols)

        # ── Enrichment (Composite: GeoEnricher → RiskClassifier) ──────────────
        if not df.empty:
            df = self.enricher.enrich(df)

        # ── Deduplication via DuckDB ───────────────────────────────────────────
        with duckdb.connect() as conn:
            conn.register("rows", df)
            conn.execute("""
                CREATE OR REPLACE TABLE silver AS
                SELECT * FROM (
                    SELECT *, row_number() OVER (PARTITION BY id ORDER BY updated DESC) as rn
                    FROM rows
                ) WHERE rn = 1;
            """)

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
                self.storage.upload_file(
                    local_path=local_path,
                    key=silver_key,
                    content_type="application/octet-stream",
                )

        return silver_key

    def _execute(self, **kwargs):
        return self.run(**kwargs)