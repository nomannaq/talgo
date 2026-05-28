"""
Example strategy: Simple momentum (moving average crossover on 1-min candles).

Buy when fast MA crosses above slow MA, sell when it crosses below.
"""

from __future__ import annotations

import pandas as pd

from talgo.strategy.base import Strategy


class MACrossover(Strategy):
    """
    Moving average crossover strategy.

    Params
    ------
    fast : int   — fast MA period (default 10)
    slow : int   — slow MA period (default 50)
    """

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        fast = self.params.get("fast", 10)
        slow = self.params.get("slow", 50)

        close = data["close"]
        fast_ma = close.rolling(fast).mean()
        slow_ma = close.rolling(slow).mean()

        signal = pd.Series(0, index=data.index, name="signal")
        signal[fast_ma > slow_ma] = 1
        signal[fast_ma < slow_ma] = -1

        return signal


if __name__ == "__main__":
    from talgo.analysis.metrics import print_metrics
    from talgo.backtest.engine import run_backtest
    from talgo.data.loader import get_candles

    candles = get_candles(
        "BTC-USDT", exchange="BINANCE", start="2024-01-01", end="2024-03-01"
    )

    strategy = MACrossover(params={"fast": 10, "slow": 50})
    signals = strategy.generate_signals(candles)

    result = run_backtest(candles, signals)
    print_metrics(result)
