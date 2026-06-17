"""
ISeismicDataSource — Strategy pattern interface.
Decouples pipeline jobs from a concrete HTTP client, enabling testing with mocks.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class ISeismicDataSource(ABC):
    """
    Abstract contract for any seismic event data provider.

    Pattern: Strategy
    Concrete implementations: USGSClient, MockSeismicClient (tests).
    """

    @abstractmethod
    def fetch_geojson(
        self,
        *,
        starttime: str,
        endtime: str,
        minmagnitude: float | None = None,
    ) -> bytes:
        """
        Returns raw GeoJSON bytes for the given time window.
        starttime/endtime: ISO-8601 datetime strings.
        """
        ...
