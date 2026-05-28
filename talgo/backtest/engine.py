"""
Vectorized backtesting engine.

Assumes:
- Signals are +1 (long), 0 (flat), -1 (short).
- Positions are entered at the next bar's open (or close, configurable).
- Transaction costs are applied per trade (round-trip on position change).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def run_backtest(
    candles: pd.DataFrame,
    signals: pd.Series,
    fee_rate: float = 0.0004,  # 0.04% per side (Binance taker)
    slippage: float = 0.0001,  # 0.01% per side
    initial_capital: float = 10_000.0,
    price_col: str = "close",
) -> pd.DataFrame:
    """
    Run a vectorized backtest.

    Parameters
    ----------
    candles : pd.DataFrame
        OHLCV data with DatetimeIndex.
    signals : pd.Series
        Signal series (+1, 0, -1) aligned to candles index.
    fee_rate : float
        Taker fee per side as a fraction.
    slippage : float
        Estimated slippage per side as a fraction.
    initial_capital : float
        Starting capital in quote currency.
    price_col : str
        Which price column to use for fills ('close' or 'open').

    Returns
    -------
    pd.DataFrame
        Backtest result with columns:
        signal, position, price, returns, strategy_returns, equity.
    """
    df = candles[[price_col]].copy().rename(columns={price_col: "price"})
    df["signal"] = signals.reindex(df.index).fillna(0)

    # Shift signals by 1 bar: trade on next bar after signal
    df["position"] = df["signal"].shift(1).fillna(0)

    # Price returns
    df["returns"] = df["price"].pct_change()

    # Cost per bar: applied when position changes
    df["trade"] = df["position"].diff().abs()
    total_cost_per_side = fee_rate + slippage
    df["cost"] = df["trade"] * total_cost_per_side * 2  # round-trip

    # Strategy returns
    df["strategy_returns"] = df["position"] * df["returns"] - df["cost"]

    # Equity curve
    df["equity"] = initial_capital * (1 + df["strategy_returns"]).cumprod()

    return df.dropna()
