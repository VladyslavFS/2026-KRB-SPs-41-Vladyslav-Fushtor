from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from pipeline.protocols.job import BaseJob
from pipeline.protocols.seismic_source import ISeismicDataSource
from pipeline.config.settings import Settings
from pipeline.storage.storage import ObjectStorage


@dataclass
class BronzeIngestJob(BaseJob):
    """
    Fetches raw GeoJSON from a seismic data source and stores it as a raw object.

    Pattern:
      - BaseJob (Template Method) for uniform job interface.
      - ISeismicDataSource (Strategy) — injectable client (USGS or mock).
      - ObjectStorage (Strategy) — injectable storage backend.
    """
    settings: Settings
    storage: ObjectStorage
    client: ISeismicDataSource          # ← was hardcoded USGSClient

    def run(self, *, window_start: datetime, window_end: datetime) -> str:
        """Fetches GeoJSON and stores it. Returns storage key."""
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)
        if window_end.tzinfo is None:
            window_end = window_end.replace(tzinfo=timezone.utc)

        raw_bytes = self.client.fetch_geojson(
            starttime=window_start.isoformat(),
            endtime=window_end.isoformat(),
        )

        key = (
            "raw/earthquake/"
            f"date={window_start.date().isoformat()}/"
            f"hour={window_start.hour:02d}/"
            f"earthquake_{window_start.strftime('%Y%m%dT%H%M%SZ')}"
            f"_{window_end.strftime('%Y%m%dT%H%M%SZ')}.geojson"
        )

        self.storage.put_bytes(
            key=key,
            data=raw_bytes,
            content_type="application/geo+json",
        )
        return key

    def _execute(self, **kwargs):
        return self.run(**kwargs)