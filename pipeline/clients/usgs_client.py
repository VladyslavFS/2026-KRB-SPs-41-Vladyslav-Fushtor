from __future__ import annotations

import requests


class USGSClient:
    BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    def fetch_geojson(self, *, starttime: str, endtime: str, minmagnitude: float) -> bytes:
        """
        Returns raw GeoJSON bytes.
        starttime/endtime: ISO dates or datetime strings accepted by USGS (e.g. 2026-01-20T00:00:00)
        """
        params = {
            "format": "geojson",
            "starttime": starttime,
            "endtime": endtime,
            "minmagnitude": minmagnitude,
            "orderby": "time",
        }

        response = requests.get(self.BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        return response.content