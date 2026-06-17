"""
BaseJob — Template Method pattern.
All pipeline jobs must inherit this and implement run().
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseJob(ABC):
    """
    Abstract base for all pipeline jobs.

    Pattern: Template Method
    Every Job has exactly one entry-point: run(**kwargs).
    Concrete jobs implement _execute() with their specific logic,
    while base class can provide cross-cutting concerns (logging, timing, etc.).
    """

    def run(self, **kwargs: Any) -> Any:
        """
        Public entry-point. Delegates to _execute().
        Subclasses that need custom signatures should override run() directly
        (keeping the ABC contract via _execute as optional hook).
        """
        return self._execute(**kwargs)

    @abstractmethod
    def _execute(self, **kwargs: Any) -> Any:
        """
        Implement the job-specific logic here.
        Override run() directly for jobs that need typed kwargs.
        """
        ...
