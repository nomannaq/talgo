"""Abstract base class for all trading strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    """
    Base class for all strategies.

    Subclasses must implement `generate_signals`, which takes a feature
    DataFrame and returns a signal Series:
        +1  → long
         0  → flat
        -1  → short
    """

    def __init__(self, params: dict | None = None):
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals from feature data.

        Parameters
        ----------
        data : pd.DataFrame
            Feature DataFrame with a DatetimeIndex.

        Returns
        -------
        pd.Series
            Integer signal series (+1, 0, -1) aligned to data's index.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(params={self.params})"
