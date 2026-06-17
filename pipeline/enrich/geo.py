from __future__ import annotations

import logging
import reverse_geocoder as rg
import pandas as pd

from pipeline.protocols.enricher import IEnricher

# Suppress verbose logging from reverse_geocoder on import
logging.getLogger("reverse_geocoder").setLevel(logging.ERROR)


def get_country_code(lat: float, lon: float) -> str | None:
    """
    Returns 2-letter country code (ISO 3166-1 alpha-2) for given coordinates.
    Uses offline K-D tree (fast, ~20MB memory).
    Example: (35.68, 139.76) -> 'JP'
    """
    if lat is None or lon is None:
        return None

    try:
        results = rg.search((lat, lon), mode=1)
        if results:
            return results[0].get("cc")
    except Exception:
        return None

    return None


class GeoEnricher(IEnricher):
    """
    Adds 'country' column (ISO 3166-1 alpha-2) to a DataFrame
    using offline reverse geocoding (no network required).

    Pattern: Strategy — pluggable into CompositeEnricher.
    """

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["country"] = df.apply(
            lambda r: get_country_code(
                r.get("latitude") if isinstance(r, dict) else r["latitude"],
                r.get("longitude") if isinstance(r, dict) else r["longitude"],
            ),
            axis=1,
        )
        return df