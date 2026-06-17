"""
OOP Protocol / Interface layer for the pipeline.
All abstract base classes (ABC) that define contracts live here.
"""
from pipeline.protocols.job import BaseJob
from pipeline.protocols.seismic_source import ISeismicDataSource
from pipeline.protocols.enricher import IEnricher

__all__ = ["BaseJob", "ISeismicDataSource", "IEnricher"]
