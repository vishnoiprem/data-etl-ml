"""Prometheus metrics for the pipeline.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

from prometheus_client import Counter, Histogram, start_http_server

from src.config import settings

# Counters
TWEETS_SCRAPED = Counter(
    "tweets_scraped_total",
    "Tweets successfully scraped",
    ["adapter"],
)
TWEETS_SCORED = Counter(
    "tweets_scored_total",
    "Tweets sentiment-scored by FinBERT",
)
SIGNALS_GENERATED = Counter(
    "signals_generated_total",
    "Signals generated",
    ["action"],
)
PAPER_TRADES = Counter(
    "paper_trades_total",
    "Paper-trade fills",
    ["side"],
)
PIPELINE_ERRORS = Counter(
    "pipeline_errors_total",
    "Pipeline errors",
    ["stage"],
)

# Histograms
SCRAPE_LATENCY = Histogram(
    "scrape_latency_seconds",
    "Source adapter latency",
    ["adapter"],
)
SCORE_LATENCY = Histogram(
    "score_latency_seconds",
    "FinBERT batch scoring latency",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)
SIGNAL_LATENCY = Histogram(
    "signal_latency_seconds",
    "End-to-end signal latency (scrape → store)",
)


def start_metrics_server() -> None:
    """Start the Prometheus /metrics HTTP server on PROMETHEUS_PORT."""
    try:
        start_http_server(settings.prometheus_port)
    except OSError as e:
        # port in use; not fatal
        from loguru import logger
        logger.warning(f"prometheus port {settings.prometheus_port} in use: {e}")
