"""Performance metrics for backtest results."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_metrics(backtest_df: pd.DataFrame, periods_per_year: int = 525_600) -> dict:
    """
    Compute standard performance metrics from a backtest DataFrame.

    Parameters
    ----------
    backtest_df : pd.DataFrame
        Output of `run_backtest`.
    periods_per_year : int
        Number of bars per year. Default is 525,600 (1-minute bars).

    Returns
    -------
    dict
        Dictionary of performance metrics.
    """
    r = backtest_df["strategy_returns"].dropna()
    equity = backtest_df["equity"].dropna()

    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    ann_return = (1 + total_return) ** (periods_per_year / len(r)) - 1
    ann_vol = r.std() * np.sqrt(periods_per_year)
    sharpe = ann_return / ann_vol if ann_vol > 0 else np.nan

    downside = r[r < 0].std() * np.sqrt(periods_per_year)
    sortino = ann_return / downside if downside > 0 else np.nan

    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    trades = backtest_df["trade"].sum() / 2  # round-trips
    wins = (r > 0).sum()
    hit_rate = wins / len(r) if len(r) > 0 else np.nan

    calmar = ann_return / abs(max_drawdown) if max_drawdown != 0 else np.nan

    return {
        "total_return": round(total_return, 4),
        "ann_return": round(ann_return, 4),
        "ann_volatility": round(ann_vol, 4),
        "sharpe_ratio": round(sharpe, 4),
        "sortino_ratio": round(sortino, 4),
        "calmar_ratio": round(calmar, 4),
        "max_drawdown": round(max_drawdown, 4),
        "num_trades": int(trades),
        "hit_rate": round(hit_rate, 4),
    }


def print_metrics(backtest_df: pd.DataFrame, periods_per_year: int = 525_600) -> None:
    """Pretty-print performance metrics."""
    m = compute_metrics(backtest_df, periods_per_year)
    width = 22
    print("=" * 35)
    print("  Performance Summary")
    print("=" * 35)
    for k, v in m.items():
        label = k.replace("_", " ").title()
        if (
            "return" in k
            or "drawdown" in k
            or "volatility" in k
            or "rate" in k
            and "sharpe" not in k
        ):
            print(f"  {label:<{width}} {v:.2%}")
        else:
            print(f"  {label:<{width}} {v}")
    print("=" * 35)
