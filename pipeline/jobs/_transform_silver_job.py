from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SilverTransformJob:
    """
    Converts raw USGS GeoJSON to normalized row dicts for DWH load.
    """
    
    def _clear_duplicates(self, values_to_upsert: list[dict]):
        by_id = {}
        for row in values_to_upsert:
            existing = by_id.get(row["id"])
            if not existing or existing["updated"] < row["updated"]:
                by_id[row["id"]] = row

        return list(by_id.values())
    
    def run(
        self,
        *,
        raw_geojson: bytes,
        source_window_start: datetime,
        source_window_end: datetime,
    ) -> list[dict]:
        if source_window_start.tzinfo is None:
            source_window_start = source_window_start.replace(tzinfo=timezone.utc)
        if source_window_end.tzinfo is None:
            source_window_end = source_window_end.replace(tzinfo=timezone.utc)

        payload = json.loads(raw_geojson.decode())

        features = payload.get("features", [])
        out: list[dict] = []

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

            t_ms = props.get("time")
            u_ms = props.get("updated")
            if t_ms is None or u_ms is None:
                continue

            time_dt = datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc)
            updated_dt = datetime.fromtimestamp(u_ms / 1000, tz=timezone.utc)

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
                "source_window_start": source_window_start,
                "source_window_end": source_window_end,
            }
            out.append(row)

        return self._clear_duplicates(out)
        