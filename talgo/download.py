#!/usr/bin/env python3
"""
Crypto-Lake Data Downloader
BTC-USDT-PERP only, everything from 2023-01-01
"""

import datetime
import os
import platform
import sys
import time
from pathlib import Path

import lakeapi
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# CREDENTIALS
# Set these in your .env file or as environment variables:
#   AWS_ACCESS_KEY_ID=your_key
#   AWS_SECRET_ACCESS_KEY=your_secret
# lakeapi picks them up automatically via boto3 → env vars or ~/.aws/credentials
# ─────────────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv

# Try common .env locations (repo root, current working directory, script directory)
ENV_PATHS = [
    Path.cwd() / ".env",
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]
LOADED_ENV_PATH = None
for env_path in ENV_PATHS:
    if env_path.exists():
        load_dotenv(env_path)
        LOADED_ENV_PATH = env_path
        break

# boto3 will read AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from the environment.
# You can also override them directly here for quick testing (not recommended):
# os.environ["AWS_ACCESS_KEY_ID"] = "your_key"
# os.environ["AWS_SECRET_ACCESS_KEY"] = "your_secret"

# Create a single reusable boto3 session for all downloads
import boto3

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-west-1")

if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    BOTO_SESSION = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_DEFAULT_REGION,
    )
else:
    BOTO_SESSION = boto3.Session(region_name=AWS_DEFAULT_REGION)

# ─────────────────────────────────────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

if platform.system() == "Darwin":  # macOS
    OUTPUT_DIR = Path("/Volumes/KINGSTON/lake_data")
else:  # Linux (Pi)
    OUTPUT_DIR = Path("/storage/lake_data")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXCHANGE = "BINANCE_FUTURES"
START_DATE = datetime.date(2023, 1, 1)
END_DATE = datetime.date(2026, 3, 18)

# ─────────────────────────────────────────────────────────────────────────────
# DOWNLOAD LIST  (BTC-USDT-PERP only)
# ─────────────────────────────────────────────────────────────────────────────

DOWNLOADS = [
    # ── Tier 1: Small files ───────────────────────────────────────────────────
    {
        "table": "liquidations",
        "symbols": ["BTC-USDT-PERP"],
        "start": START_DATE,
        "end": END_DATE,
        "why": "Ground truth liquidation events — core signal",
        "tier": 1,
    },
    {
        "table": "funding",
        "symbols": ["BTC-USDT-PERP"],
        "start": START_DATE,
        "end": END_DATE,
        "why": "Pre-cascade conditions + funding arbitrage",
        "tier": 1,
    },
    {
        "table": "open_interest",
        "symbols": ["BTC-USDT-PERP"],
        "start": START_DATE,
        "end": END_DATE,
        "why": "OI quality filter — OI drop after cascade = cleanup signal",
        "tier": 1,
    },
    {
        "table": "candles",
        "symbols": ["BTC-USDT-PERP"],
        "start": START_DATE,
        "end": END_DATE,
        "why": "1-minute OHLCV — regime context, volatility features",
        "tier": 1,
    },
    # ── Tier 2: Medium files ──────────────────────────────────────────────────
    {
        "table": "book_1m",
        "symbols": ["BTC-USDT-PERP"],
        "start": START_DATE,
        "end": END_DATE,
        "why": "1-min order book — spread, depth, imbalance features",
        "tier": 2,
    },
    {
        "table": "level_1",
        "symbols": ["BTC-USDT-PERP"],
        "start": START_DATE,
        "end": END_DATE,
        "why": "Best bid/ask tick data — spread during cascades",
        "tier": 2,
    },
    # ── Tier 3: Large files — run overnight ───────────────────────────────────
    # Trades split into 6-month chunks to stay within 300 GB monthly limit
    {
        "table": "trades",
        "symbols": ["BTC-USDT-PERP"],
        "start": datetime.date(2023, 1, 1),
        "end": datetime.date(2023, 6, 30),
        "why": "Tick trades H1 2023 — OFI features, cascade timing",
        "tier": 3,
    },
    {
        "table": "trades",
        "symbols": ["BTC-USDT-PERP"],
        "start": datetime.date(2023, 7, 1),
        "end": datetime.date(2023, 12, 31),
        "why": "Tick trades H2 2023",
        "tier": 3,
    },
    {
        "table": "trades",
        "symbols": ["BTC-USDT-PERP"],
        "start": datetime.date(2024, 1, 1),
        "end": datetime.date(2024, 6, 30),
        "why": "Tick trades H1 2024 — includes ETF approval + halving",
        "tier": 3,
    },
    {
        "table": "trades",
        "symbols": ["BTC-USDT-PERP"],
        "start": datetime.date(2024, 7, 1),
        "end": datetime.date(2024, 12, 31),
        "why": "Tick trades H2 2024 — includes August crash + election rally",
        "tier": 3,
    },
    {
        "table": "trades",
        "symbols": ["BTC-USDT-PERP"],
        "start": datetime.date(2025, 1, 1),
        "end": END_DATE,
        "why": "Tick trades 2025 to end date",
        "tier": 3,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# DOWNLOADER
# ─────────────────────────────────────────────────────────────────────────────


def output_path(job: dict) -> Path:
    symbols_str = "_".join(s.replace("-", "").replace("PERP", "") for s in job["symbols"])
    filename = f"{job['table']}_{symbols_str}_{job['start']}_{job['end']}.parquet"
    return OUTPUT_DIR / job["table"] / filename


def download_job(job: dict) -> bool:
    out = output_path(job)
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists():
        mb = out.stat().st_size / 1024 / 1024
        print(f"  ✓ exists ({mb:.0f} MB) — {out.name}")
        return True

    symbols_label = ", ".join(job["symbols"])
    print(f"  ↓  {job['table']}  [{symbols_label}]  {job['start']} → {job['end']}")
    print(f"     {job['why']}")

    try:
        df = lakeapi.load_data(
            table=job["table"],
            start=datetime.datetime.combine(job["start"], datetime.time.min),
            end=datetime.datetime.combine(job["end"], datetime.time.max),
            symbols=job["symbols"],
            exchanges=[EXCHANGE],
            boto3_session=BOTO_SESSION,
        )

        if df is None or df.empty:
            print(f"  ⚠  No data returned")
            return False

        df.columns = [c.lower() for c in df.columns]
        df.to_parquet(out, compression="snappy", index=False)

        mb = out.stat().st_size / 1024 / 1024
        print(f"  ✓  {len(df):,} rows  →  {mb:.0f} MB  saved\n")
        return True

    except Exception as e:
        print(f"  ✗  ERROR: {e}\n")
        return False


def check_usage():
    try:
        # NOTE: some lakeapi versions break when passing boto3_session as a named
        # argument due to an internal cache key lambda. Positional call is safer.
        try:
            result = lakeapi.used_data(BOTO_SESSION)
        except TypeError:
            result = lakeapi.used_data()

        # Newer versions return a dict, older may return a float-like value.
        gb = result.get("downloaded_gb", 0.0) if isinstance(result, dict) else float(result)

        bar_filled = max(0, min(40, int(gb / 300 * 40)))
        bar = "█" * bar_filled + "░" * (40 - bar_filled)
        pct = gb / 300 * 100
        print(f"\n  Monthly usage: [{bar}] {gb:.1f} / 300 GB ({pct:.1f}%)")
        if gb > 250:
            print("  ⚠️  WARNING: Near 300 GB limit — pause downloads!")
        elif gb > 200:
            print("  ⚠️  CAUTION: Over 200 GB used")
    except Exception as e:
        print(f"  Could not fetch usage: {e}")


def ensure_credentials() -> bool:
    """Validate that boto3 can resolve AWS credentials for lakeapi calls."""
    creds = BOTO_SESSION.get_credentials()
    if creds and creds.access_key:
        return True

    print("\n✗ AWS credentials not found.")
    print("  Expected: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
    if LOADED_ENV_PATH:
        print(f"  .env loaded from: {LOADED_ENV_PATH}")
    else:
        print("  .env file not found in expected locations.")
    print("  Try placing .env in repo root and rerun.")
    return False


def show_summary():
    print(f"\n{'─' * 55}")
    print(f"  {'TABLE':<20} {'FILES':>6}  {'SIZE':>10}")
    print(f"{'─' * 55}")

    total = 0
    for folder in sorted(OUTPUT_DIR.iterdir()):
        if not folder.is_dir():
            continue
        files = list(folder.glob("*.parquet"))
        if not files:
            continue
        size = sum(f.stat().st_size for f in files)
        total += size
        print(f"  {folder.name:<20} {len(files):>6}  {size / 1024 / 1024:>8.0f} MB")

    print(f"{'─' * 55}")
    print(f"  {'TOTAL':<20} {'':>6}  {total / 1024 / 1024 / 1024:>8.2f} GB\n")


def run_tier(tier: int):
    jobs = [j for j in DOWNLOADS if j["tier"] == tier]

    tier_labels = {
        1: "Small files  (liquidations, funding, OI, candles)",
        2: "Medium files (order book 1m, level_1)",
        3: "Large files  (tick trades — run overnight)",
    }

    print(f"\n{'═' * 55}")
    print(f"  TIER {tier}: {tier_labels.get(tier, '')}")
    print(f"  {len(jobs)} downloads")
    print(f"{'═' * 55}\n")

    check_usage()
    print()

    ok = fail = 0
    for i, job in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}]")
        if download_job(job):
            ok += 1
        else:
            fail += 1
        time.sleep(1)

    print(f"\n  Tier {tier}: {ok} ok, {fail} failed")
    show_summary()
    check_usage()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    # Commands that require AWS auth to talk to lakeapi
    if cmd in {"1", "2", "3", "all", "usage"} and not ensure_credentials():
        sys.exit(1)

    if cmd == "1":
        run_tier(1)
        print("\n✅ Done. Run: python3 download.py 2")

    elif cmd == "2":
        run_tier(2)
        print("\n✅ Done. Run overnight: python3 download.py 3")

    elif cmd == "3":
        run_tier(3)
        print("\n✅ Full dataset ready.")

    elif cmd == "all":
        for t in (1, 2, 3):
            run_tier(t)

    elif cmd == "summary":
        show_summary()
        check_usage()

    elif cmd == "usage":
        check_usage()

    else:
        print("""
  Crypto-Lake Downloader — BTC-USDT-PERP

  python3 download.py 1        Small files   (liquidations, funding, OI, candles)
  python3 download.py 2        Medium files  (book_1m, level_1)
  python3 download.py 3        Tick trades   (~50 GB, run overnight)
  python3 download.py all      Everything
  python3 download.py summary  What you have on disk
  python3 download.py usage    GB used this month
        """)
