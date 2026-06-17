from __future__ import annotations

import requests

from pipeline.protocols.seismic_source import ISeismicDataSource


class USGSClient(ISeismicDataSource):
    """
    USGS Earthquake Hazards Program FDSN Web Service client.

    Pattern: Strategy — implements ISeismicDataSource.
    Can be substituted with MockSeismicClient in tests without network.
    """

    BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    def fetch_geojson(
        self,
        *,
        starttime: str,
        endtime: str,
        minmagnitude: float | None = None,
    ) -> bytes:
        """
        Returns raw GeoJSON bytes.
        starttime/endtime: ISO dates or datetime strings accepted by USGS
        (e.g. 2026-01-20T00:00:00).
        """
        params: dict = {
            "format": "geojson",
            "starttime": starttime,
            "endtime": endtime,
            "orderby": "time",
        }
        if minmagnitude is not None:
            params["minmagnitude"] = minmagnitude

        response = requests.get(self.BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        return response.content