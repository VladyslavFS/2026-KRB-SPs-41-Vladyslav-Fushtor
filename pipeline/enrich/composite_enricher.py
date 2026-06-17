"""
CompositeEnricher — Composite pattern.
Chains multiple IEnricher instances into a single enricher.
"""
from __future__ import annotations

import pandas as pd

from pipeline.protocols.enricher import IEnricher


class CompositeEnricher(IEnricher):
    """
    Applies a sequence of IEnricher instances in order.

    Pattern: Composite — treats a group of enrichers as a single enricher.

    Usage:
        enricher = CompositeEnricher(GeoEnricher(), RiskClassifier())
        df = enricher.enrich(df)
    """

    def __init__(self, *enrichers: IEnricher) -> None:
        if not enrichers:
            raise ValueError("CompositeEnricher requires at least one enricher.")
        self._enrichers = enrichers

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        for enricher in self._enrichers:
            df = enricher.enrich(df)
        return df

    def __repr__(self) -> str:
        names = ", ".join(type(e).__name__ for e in self._enrichers)
        return f"CompositeEnricher({names})"
