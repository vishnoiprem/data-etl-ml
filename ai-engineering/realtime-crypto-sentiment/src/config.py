"""Configuration: env-driven singleton.

Author: Prem Vishnoi <pvishnoi@avilx.com>

All knobs live in .env. This module is the single source of truth.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Project-wide settings, loaded from .env at import time."""

    model_config = SettingsConfigDict(
        env_file=REPO / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Storage ───────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/crypto"
    )

    # ── Prices ────────────────────────────────────────────────────────────
    binance_ws: str = "wss://stream.binance.com:9443/stream"
    binance_rest: str = "https://api.binance.com"
    symbols: List[str] = Field(
        default_factory=lambda: ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "MATIC"]
    )
    backfill_days: int = 7

    # ── Sources (Nitter / Syndication) ─────────────────────────────────────
    mirrors: List[str] = Field(
        default_factory=lambda: [
            "nitter.net",
            "nitter.privacydev.net",
            "nitter.poast.org",
            "nitter.1d4.us",
        ]
    )
    scrape_interval_sec: int = 60
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    )

    # ── Topics ────────────────────────────────────────────────────────────
    cashtags: List[str] = Field(
        default_factory=lambda: [
            "$BTC", "$ETH", "$SOL", "$BNB", "$XRP", "$DOGE", "$ADA", "$AVAX", "$LINK", "$MATIC",
        ]
    )
    hashtags: List[str] = Field(
        default_factory=lambda: [
            "#bitcoin", "#ethereum", "#solana", "#bnb", "#xrp", "#dogecoin",
            "#ada", "#avax", "#chainlink", "#matic", "#memecoin", "#altcoin",
        ]
    )
    keywords: List[str] = Field(
        default_factory=lambda: [
            "bitcoin", "ethereum", "solana", "binance coin", "ripple",
            "dogecoin", "cardano", "avalanche", "chainlink", "polygon",
        ]
    )

    # ── ML ────────────────────────────────────────────────────────────────
    finbert_model: str = "ProsusAI/finbert"
    finbert_batch_size: int = 32

    # ── Paper trader ──────────────────────────────────────────────────────
    starting_cash_usd: float = 10_000.0
    max_position_pct: float = 5.0
    max_open_positions: int = 3
    fee_bps: int = 10  # basis points (0.1% = 10 bps)

    # ── Signals ───────────────────────────────────────────────────────────
    signal_threshold: float = 1.0
    sentiment_weight: float = 0.6
    momentum_weight: float = 0.4
    signal_lookback_hours: int = 24

    # ── Pipeline ──────────────────────────────────────────────────────────
    score_interval_sec: int = 60
    signal_interval_sec: int = 60
    trade_interval_sec: int = 5

    # ── Observability ─────────────────────────────────────────────────────
    prometheus_port: int = 8000
    log_level: str = "INFO"

    @field_validator("symbols", "mirrors", "cashtags", "hashtags", "keywords", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @property
    def symbols_with_usdt(self) -> List[str]:
        return [f"{s}USDT" for s in self.symbols]

    @property
    def all_topics(self) -> List[str]:
        return self.cashtags + self.hashtags + self.keywords

    @property
    def fee_fraction(self) -> float:
        return self.fee_bps / 10_000.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Module-level singleton for `from src.config import settings`
settings = get_settings()
