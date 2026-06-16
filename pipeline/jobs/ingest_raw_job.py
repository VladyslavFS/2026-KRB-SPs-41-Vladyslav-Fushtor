from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from pipeline.clients.usgs_client import USGSClient
from pipeline.config.settings import Settings
from pipeline.storage.storage import ObjectStorage


@dataclass
class BronzeIngestJob:
    settings: Settings
    storage: ObjectStorage
    client: USGSClient

    def run(self, *, window_start: datetime, window_end: datetime) -> str:
        """
        Fetches GeoJSON from USGS and stores it as raw object.
        Returns storage key.
        """
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)
        if window_end.tzinfo is None:
            window_end = window_end.replace(tzinfo=timezone.utc)

        start_s = window_start.isoformat()
        end_s = window_end.isoformat()

        raw_bytes = self.client.fetch_geojson(
            starttime=start_s,
            endtime=end_s
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
            content_type="application/geo+json"
        )
        return key