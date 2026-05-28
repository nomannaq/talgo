# talgo — Crypto Quantitative Strategies

A research-grade framework for downloading crypto market data and building quantitative trading strategies.

## Data Source

Data is sourced from [crypto-lake](https://crypto-lake.com/data/) via the `lakeapi` Python package.

Supported data types:
- `candles` — 1-minute OHLCV
- `trades` — aggregated taker trades
- `level_1` — best bid/ask snapshots
- `book` / `book_1m` — full order book snapshots
- `funding` — funding rate + mark price (perps)
- `open_interest` — open interest (perps)
- `liquidations` — liquidation events (perps)

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -e ".[research,backtest,dev]"

# 3. Configure your API key
cp .env.example .env
# Edit .env and set LAKE_API_KEY=your_key_here
```

## Project Structure

```
talgo/          Core package
  data/         Data loaders + feature engineering
  strategy/     Abstract Strategy base class
  backtest/     Vectorized backtest engine
  analysis/     Performance metrics
  utils/        Config & env loading
strategies/     Concrete strategy implementations
notebooks/      Research notebooks
tests/          Unit tests
data/           Local parquet cache (gitignored)
```

## Quick Start

```python
from talgo.data.loader import get_candles
from talgo.backtest.engine import run_backtest
from talgo.analysis.metrics import print_metrics
from strategies.example_momentum import MACrossover

candles = get_candles("BTC-USDT", start="2024-01-01", end="2024-03-01")
strategy = MACrossover(params={"fast": 10, "slow": 50})
signals = strategy.generate_signals(candles)
result = run_backtest(candles, signals)
print_metrics(result)
```

## Running Tests

```bash
pytest
```

## Linting

```bash
ruff check .
ruff format .
```
