"""
Configuration and environment loading.

Place secrets in a .env file at the project root (never commit it).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root
load_dotenv(Path(__file__).resolve().parents[3] / ".env")


@dataclass
class Settings:
    aws_access_key_id: str = field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID", ""))
    aws_secret_access_key: str = field(
        default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY", "")
    )
    lake_cache_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("LAKE_CACHE_PATH", Path(__file__).resolve().parents[3] / ".lake_cache")
        )
    )
    default_exchange: str = field(
        default_factory=lambda: os.getenv("DEFAULT_EXCHANGE", "BINANCE_FUTURES")
    )

    def validate(self) -> None:
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            raise EnvironmentError(
                "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set in your .env file."
            )


settings = Settings()
