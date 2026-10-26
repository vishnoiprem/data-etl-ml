"""Healthcheck CLI: print a one-line summary of which data sources are
reachable, then exit non-zero if NONE are reachable.

Useful for:
  - Docker HEALTHCHECK (every 60s)
  - Kubernetes livenessProbe
  - Local debugging ("is my APIFY_TOKEN working?")

Exit codes:
  0 — at least one adapter is healthy
  1 — no adapter is healthy (operator should investigate)
  2 — DB unreachable (separate failure mode)

Usage:
  python scripts/healthcheck.py
  python scripts/healthcheck.py --json   # machine-readable output
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as `python scripts/healthcheck.py` from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from loguru import logger

from src.config import settings
from src.sources.registry import SourceRegistry
from src.store import db


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline healthcheck")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    report: dict = {
        "db_url": settings.database_url,
        "apify_token_configured": bool(settings.apify_token),
        "tracked_tags": settings.tracked_tags,
    }

    # ── DB reachability ────────────────────────────────────────────
    try:
        engine = db.get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        report["db_ok"] = True
    except Exception as e:
        report["db_ok"] = False
        report["db_error"] = str(e)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"DB UNREACHABLE: {e}")
        return 2

    # ── Source reachability ────────────────────────────────────────
    source = SourceRegistry.from_settings()
    report["apify_configured"] = source.apify is not None
    report["apify_healthy"] = source.apify.is_healthy() if source.apify else False
    report["nitter_healthy"] = source.nitter.is_healthy()
    report["syndication_healthy"] = source.syndication.is_healthy()
    report["any_healthy"] = source.is_healthy()
    report["active_source"] = source.active

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"DB:            {'✓' if report['db_ok'] else '✗'}")
        print(f"Apify:         {'✓' if report['apify_healthy'] else '✗'} "
              f"(token={'set' if report['apify_token_configured'] else 'unset'})")
        print(f"Nitter:        {'✓' if report['nitter_healthy'] else '✗'}")
        print(f"Syndication:   {'✓' if report['syndication_healthy'] else '✗'}")
        print(f"Active:        {report['active_source']}")

    return 0 if report["any_healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
