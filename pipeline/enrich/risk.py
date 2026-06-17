from __future__ import annotations

import pandas as pd

from pipeline.protocols.enricher import IEnricher


def calculate_risk_class(mag: float | None, depth: float | None) -> str:
    """
    Calculates seismic risk class based on magnitude and depth.
    Returns: 'HIGH', 'MED', 'LOW' or 'UNKNOWN'.
    """
    if mag is None:
        return "UNKNOWN"

    if mag >= 6.0:
        return "HIGH"

    if mag >= 4.5:
        return "MED"

    # Shallow earthquakes are more dangerous even if magnitude is smaller
    if mag >= 3.0 and depth is not None and depth < 10.0:
        return "MED"

    return "LOW"


class RiskClassifier(IEnricher):
    """
    Adds 'risk_class' column ('HIGH' | 'MED' | 'LOW' | 'UNKNOWN') to a DataFrame
    based on magnitude and depth.

    Pattern: Strategy — pluggable into CompositeEnricher.
    """

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["risk_class"] = df.apply(
            lambda r: calculate_risk_class(r.get("mag"), r.get("depth")),
            axis=1,
        )
        return df