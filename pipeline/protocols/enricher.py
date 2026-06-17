"""
IEnricher — Strategy + Composite pattern interface.
Enrichers receive a DataFrame and return an enriched DataFrame.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class IEnricher(ABC):
    """
    Abstract contract for DataFrame enrichers.

    Pattern: Strategy (swappable implementations) + Composite (CompositeEnricher)
    Concrete implementations: GeoEnricher, RiskClassifier, CompositeEnricher.
    """

    @abstractmethod
    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Receives a DataFrame, adds/modifies columns, returns enriched DataFrame.
        Must not mutate the input in-place if caller expects immutability.
        """
        ...
