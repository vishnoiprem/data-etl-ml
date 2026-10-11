"""Configuration: env-driven singleton.

Author: Prem Vishnoi <pvishnoi@avilx.com>

All knobs live in .env. This module is the single source of truth.

Project is now a domain-agnostic real-time X.com sentiment analytics
tool with a paper-trading simulator. There is no live price feed —
the broker uses synthetic prices derived from tweet engagement.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

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
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/sentiment"
    )

    # ── Sources (Nitter / Syndication) ─────────────────────────────────────
    mirrors: list[str] = Field(
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

    # ── Tracked tags (per-tag dashboard grouping) ─────────────────────────
    # Topics the pipeline scrapes every cycle and routes tweets to.
    # These are free-text search queries; the trending-tag extractor pulls
    # the actual cashtags/hashtags/keywords from the returned tweets.
    tracked_tags: list[str] = Field(
        default_factory=lambda: [
            # AI / Data
            "AI", "LLM", "data engineering", "vector database",
            # Stocks
            "S&P 500", "nasdaq", "TSLA", "NVDA",
        ]
    )

    # ── Trending tags (free-text queries scraped for tag discovery) ───────
    # Mix of verticals so the dashboard's top-10 isn't single-domain.
    trending_queries: list[str] = Field(
        default_factory=lambda: [
            # AI / Data
            "AI", "data engineering", "LLM", "vector database",
            # Stocks
            "S&P 500", "nasdaq", "TSLA", "NVDA",
            # Dating
            "dating", "girlf", "girlfriend", "tiktok dating",
        ]
    )
    trending_window_minutes: int = 5
    trending_top_n: int = 10

    # ── ML (Twitter sentiment) ────────────────────────────────────────────
    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    sentiment_batch_size: int = 32

    # ── Paper trader ──────────────────────────────────────────────────────
    # "Units" — generic; the broker has no real-money concept.
    starting_units: float = 10_000.0
    max_position_pct: float = 5.0
    max_open_positions: int = 3
    fee_bps: int = 10  # basis points (0.1% = 10 bps)

    # ── Signals ───────────────────────────────────────────────────────────
    signal_threshold: float = 1.0
    signal_lookback_hours: int = 24

    # ── Pipeline ──────────────────────────────────────────────────────────
    score_interval_sec: int = 60
    signal_interval_sec: int = 60
    trade_interval_sec: int = 5

    # ── Observability ─────────────────────────────────────────────────────
    prometheus_port: int = 8000
    log_level: str = "INFO"

    @field_validator("mirrors", "tracked_tags", "trending_queries", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @property
    def fee_fraction(self) -> float:
        return self.fee_bps / 10_000.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Module-level singleton for `from src.config import settings`
settings = get_settings()