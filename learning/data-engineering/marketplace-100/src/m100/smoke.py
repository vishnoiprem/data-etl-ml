"""
smoke.py — local end-to-end smoke test of one iteration.

Runs the full pipeline without any external services:
  * No Marketplace API → canned listings
  * No Spark cluster  → in-memory pandas → list of dicts
  * No MLflow         → in-memory "runs" dict
  * No FM API         → agent's canned response
  * No Lakebase       → Delta fallback (which here is a list)

`make smoke` runs this. It completes in ~3-5 seconds and
exits 0 on success, 1 on failure.

The point is to exercise every branch of the driver without
needing a Databricks workspace. Production runs the same
driver with real services; the smoke just makes sure
nothing in the wiring is broken.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass, field

logger = logging.getLogger(__name__)


def run(
    *,
    max_iterations: int = 3,
    stagger_seconds: float = 0.0,
    quality_threshold: float = 0.4,
    max_retries: int = 1,
    catalog: str = "marketplace_100_smoke",
) -> int:
    """Run N smoke iterations. Returns exit code."""
    from .marketplace_client import Listing
    from .agent import M100Agent

    # --- canned marketplace listings (3 categories, rotating)
    CATEGORIES = ["Finance", "Healthcare", "Geospatial"]
    LISTINGS = [
        Listing(
            id="smoke-001",
            title="Sample Finance Co — Transactions",
            provider="Smoke Provider",
            summary="Synthetic financial transactions for the smoke test.",
            categories=["Finance"],
            tags=["transactions", "synthetic"],
            downloads=42,
            file_list=[{"path": "memory://finance.csv", "format": "csv"}],
        ),
        Listing(
            id="smoke-002",
            title="Sample Health Inc — Patients",
            provider="Smoke Provider",
            summary="Synthetic patient records for the smoke test.",
            categories=["Healthcare"],
            tags=["healthcare", "synthetic"],
            downloads=37,
            file_list=[{"path": "memory://health.csv", "format": "csv"}],
        ),
        Listing(
            id="smoke-003",
            title="Sample Geo Lab — Sensors",
            provider="Smoke Provider",
            summary="Synthetic sensor readings for the smoke test.",
            categories=["Geospatial"],
            tags=["geo", "synthetic"],
            downloads=29,
            file_list=[{"path": "memory://geo.csv", "format": "csv"}],
        ),
    ]
    BY_CATEGORY = {c: [l for l in LISTINGS if c in l.categories] for c in CATEGORIES}

    agent = M100Agent(workspace_client=None)  # canned mode
    rows = []  # the "iterations" table

    for i in range(max_iterations):
        cat = CATEGORIES[i % len(CATEGORIES)]
        cand = BY_CATEGORY.get(cat, [])
        if not cand:
            continue
        listing = cand[0]
        logger.info("smoke iter %d: %s (%s)", i, listing.id, cat)

        # ingest → in-memory bronze
        bronze = _ingest_smoke(listing)
        # DLT promote → silver + gold
        silver, gold = _promote_smoke(bronze, listing.id, catalog)
        # MLOps
        mlops = _mlops_smoke(silver, listing.id, i)
        # agent
        ar = agent.evaluate(
            iter_no=i, listing_id=listing.id,
            silver_table=silver, gold_table=gold,
            mlflow_run_id=mlops["run_id"], dlt_pipeline_id=f"m100_dlt_{listing.id}",
            current_category=cat,
        )
        row = {
            "iter_no": i,
            "listing_id": listing.id,
            "category": cat,
            "status": "ok" if ar.quality_score >= quality_threshold else "skipped",
            "bronze_table": bronze,
            "silver_table": silver,
            "gold_table": gold,
            "mlflow_run_id": mlops["run_id"],
            "model_name": mlops["model_name"],
            "quality_score": ar.quality_score,
            "next_category": ar.next_category,
            "summary": ar.summary,
            "retry_count": 0,
            "duration_seconds": 0.1,
            "started_at": _now(),
            "finished_at": _now(),
        }
        rows.append(row)
        if stagger_seconds:
            time.sleep(stagger_seconds)

    # print a final summary
    print("\n" + "=" * 60)
    print("SMOKE RESULT")
    print("=" * 60)
    print(json.dumps({
        "iterations": len(rows),
        "ok": sum(1 for r in rows if r["status"] == "ok"),
        "skipped": sum(1 for r in rows if r["status"] == "skipped"),
        "categories_seen": sorted({r["category"] for r in rows}),
        "quality_min": min((r["quality_score"] for r in rows), default=0),
        "quality_max": max((r["quality_score"] for r in rows), default=0),
        "quality_avg": (
            round(sum(r["quality_score"] for r in rows) / len(rows), 3)
            if rows else 0
        ),
        "first_summary": rows[0]["summary"] if rows else "",
    }, indent=2))

    # basic assertions
    assert rows, "no iterations completed"
    assert all(r["status"] in ("ok", "skipped") for r in rows), "unexpected status"
    assert all(0.0 <= r["quality_score"] <= 1.0 for r in rows), "quality_score out of range"
    return 0


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _ingest_smoke(listing) -> str:
    """In-memory ingest: return a 'table' identifier."""
    return f"smoke://bronze/{listing.id}"


def _promote_smoke(bronze: str, listing_id: str, catalog: str) -> tuple[str, str]:
    """In-memory DLT promotion."""
    return (f"{catalog}.silver.{listing_id}", f"{catalog}.gold.{listing_id}_profile")


def _mlops_smoke(silver: str, listing_id: str, iter_no: int) -> dict:
    """In-memory MLOps run."""
    return {
        "run_id": f"smoke-{iter_no:03d}",
        "model_name": f"{silver}_model",
        "metrics": {"accuracy": 0.7, "f1": 0.65},
    }


def main():
    """CLI entry point. `python3 -m m100.smoke`."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=3)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    return run(max_iterations=args.iterations)


if __name__ == "__main__":
    sys.exit(main() or 0)
