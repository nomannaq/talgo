"""Basic smoke tests for the data loader (uses lakeapi sample data)."""

import pandas as pd
import pytest


def test_get_candles_returns_dataframe():
    from talgo.data.loader import get_candles

    df = get_candles(
        "BTC-USDT", exchange="BINANCE", start="2022-10-17", end="2022-10-18"
    )
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "close" in df.columns


def test_get_level1_returns_dataframe():
    from talgo.data.loader import get_level1

    df = get_level1(
        "BTC-USDT", exchange="BINANCE", start="2022-10-17", end="2022-10-18"
    )
    assert isinstance(df, pd.DataFrame)
    assert "bid_0_price" in df.columns
    assert "ask_0_price" in df.columns


def test_candles_index_is_datetime():
    from talgo.data.loader import get_candles

    df = get_candles(
        "BTC-USDT", exchange="BINANCE", start="2022-10-17", end="2022-10-18"
    )
    assert isinstance(df.index, pd.DatetimeIndex)
