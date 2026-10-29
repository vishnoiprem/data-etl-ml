"""
driver.py — the 100-iteration loop.

One iteration:

   1. Pick a category        (rotation + agent's last `next_category`)
   2. Search marketplace     (skip ids we've already seen)
   3. Install the listing    (skip on PersonalizationRequired)
   4. Ingest → bronze        (Delta / Auto Loader / COPY INTO)
   5. DLT  → silver + gold   (Lakeflow Declarative Pipeline)
   6. MLOps → MLflow + UC    (baseline model + Champion alias)
   7. Agent → score + next   (Mosaic AI ChatAgent + FM API)
   8. Persist                (iterations Delta + Lakebase ops log)

State lives in:
   * `<catalog>.agents.iterations`        (Delta; the truth)
   * `lakebase.iterations`                (Postgres; sub-second reads)
   * `<catalog>.agents.lakebase_fallback` (Delta; if no Lakebase)

Resumable:
   On boot, we read `MAX(iter_no) WHERE status='ok'` and
   resume from `+1`. A crash mid-iteration is detected on
   next boot (`status='running' AND started_at < now - 1h`)
   and the iteration is retried.

Self-evaluating:
   The agent returns `quality_score`. If below the threshold,
   `retry_count` is incremented; we re-pick a listing in the
   same category. After `max_retries`, we mark the iteration
   `skipped` and move on.

Free Edition posture:
   * Serverless Jobs (no all-purpose clusters)
   * Lakeflow `pipeline_task` per iteration (1-active-pipeline
     quota)
   * Foundation Model API (no dedicated serving)
   * Lakebase scale-to-zero (1 project)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class IterationRecord:
    """The full record of one iteration. Persisted to Delta + Lakebase."""
    iter_no: int
    listing_id: str
    category: str
    status: str                       # running | ok | skipped | failed
    bronze_table: str = ""
    silver_table: str = ""
    gold_table: str = ""
    mlflow_run_id: str = ""
    model_name: str = ""
    quality_score: float = 0.0
    next_category: str = ""
    summary: str = ""
    retry_count: int = 0
    duration_seconds: float = 0.0
    started_at: str = ""
    finished_at: str = ""
    cost_usd: float = 0.0            # FM API spend for this iter
    dbu: float = 0.0                 # DBU consumption for this iter
    endpoint_name: str = ""          # serving endpoint deployed for this iter
    endpoint_p95_ms: float = 0.0     # p95 latency from the monitoring probe
    endpoint_drift: float = 0.0      # drift score from the monitoring probe


def main():
    """CLI entry point. Databricks Job calls this with flags."""
    ap = argparse.ArgumentParser(description="marketplace-100 driver")
    ap.add_argument("--max-iterations", type=int, default=int(os.getenv("MAX_ITERATIONS", "100")))
    ap.add_argument("--stagger-seconds", type=int, default=int(os.getenv("STAGGER_SECONDS", "60")))
    ap.add_argument("--quality-threshold", type=float, default=float(os.getenv("QUALITY_THRESHOLD", "0.4")))
    ap.add_argument("--max-retries", type=int, default=int(os.getenv("MAX_RETRIES", "2")))
    ap.add_argument("--catalog", default=os.getenv("M100_CATALOG", "marketplace_100"))
    ap.add_argument("--max-daily-usd", type=float, default=float(os.getenv("MAX_DAILY_USD", "5.0")))
    ap.add_argument("--max-hourly-tokens", type=int, default=int(os.getenv("MAX_HOURLY_TOKENS", "200000")))
    ap.add_argument("--max-daily-dbu", type=float, default=float(os.getenv("MAX_DAILY_DBU", "5.0")))
    ap.add_argument("--no-budget-guard", action="store_true",
                    help="Disable the BudgetGuard (e.g. for paid workspaces).")
    ap.add_argument("--no-serving", action="store_true",
                    help="Skip the deploy+monitor step (e.g. in tight smoke tests).")
    ap.add_argument("--serving-probe-n", type=int,
                    default=int(os.getenv("M100_SERVING_PROBE_N", "20")),
                    help="Synthetic requests per monitoring probe.")
    ap.add_argument("--smoke", action="store_true",
                    help="Use the smoke driver (no Databricks deps; runs locally)")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.smoke:
        from .smoke import run as run_smoke
        return run_smoke(
            max_iterations=args.max_iterations,
            stagger_seconds=args.stagger_seconds,
            quality_threshold=args.quality_threshold,
            max_retries=args.max_retries,
            catalog=args.catalog,
        )

    # Production path
    from pyspark.sql import SparkSession
    from databricks.sdk import WorkspaceClient
    from .marketplace_client import MarketplaceClient, categories_to_rotate
    from .ingest import ingest_listing
    from .dlt_pipeline import promote_locally
    from .mlops import run_baseline
    from .agent import M100Agent
    from .lakebase import (
        connect, record_iteration_start, record_iteration_end,
        record_agent_call, get_max_iteration,
    )
    from .cost import (
        CostLedger, BudgetGuard, BudgetExceeded,
        read_dbu_for_iteration,
    )

    spark = SparkSession.builder.getOrCreate()
    workspace = WorkspaceClient()
    mkt = MarketplaceClient()
    catalog = args.catalog

    # History index — backs the agent's `query_history` tool.
    # Persisted to .m100_history/ in the workspace's file system
    # (or to a Volume in production; the API is the same).
    from .history_search import HistoryIndex
    history = HistoryIndex(persist_dir=os.getenv(
        "M100_HISTORY_DIR",
        f"/Workspace/Users/{os.getenv('DATABRICKS_USER', 'prem')}/m100/history"
    ))
    history.load()
    logger.info("history index: %d prior entries", history.size)

    agent = M100Agent(workspace_client=workspace, history_index=history)

    # Crash-recovery: read the highest iter_no from Lakebase.
    with connect() as conn:
        resume_from = get_max_iteration(conn) + 1
    if resume_from > 0:
        logger.info("resuming from iter_no=%d (crash recovery)", resume_from)

    # Restore the bandit state (UCB1 over categories) so we
    # don't reset to zero on every driver boot.
    from .bandit import CategoryBandit, load_from_lakebase, save_to_lakebase
    bandit = CategoryBandit()
    with connect() as conn:
        load_from_lakebase(conn, bandit)
    logger.info("bandit restored: %s", bandit.summary())

    # Cost telemetry — every FM API call is recorded; BudgetGuard
    # raises `BudgetExceeded` if the loop has spent too much.
    # Free Edition defaults: $5/day, 200k tokens/window, 5 DBU/day.
    cost_ledger = CostLedger()
    budget_guard = (
        BudgetGuard(
            max_daily_usd=args.max_daily_usd,
            max_hourly_tokens=args.max_hourly_tokens,
            max_daily_dbu=args.max_daily_dbu,
        )
        if not args.no_budget_guard
        else None
    )
    logger.info(
        "budget guard: %s",
        "disabled" if budget_guard is None else
        f"daily_usd=${args.max_daily_usd:.2f}, "
        f"hourly_tokens={args.max_hourly_tokens:,}, "
        f"daily_dbu={args.max_daily_dbu:.2f}",
    )

    next_category: Optional[str] = None
    seen_listing_ids: set[str] = set()

    for iter_no in range(resume_from, args.max_iterations):
        # 0. Budget check — bail before any work if we've spent too much.
        if budget_guard is not None:
            try:
                budget_guard.check(cost_ledger, current_iter=iter_no)
            except BudgetExceeded as e:
                logger.warning(
                    "iter %d: budget exceeded — exiting driver: %s",
                    iter_no, e,
                )
                _persist_iteration(
                    spark, conn, catalog,
                    IterationRecord(
                        iter_no=iter_no, listing_id="", category="(budget)",
                        status="skipped", summary=f"budget exceeded: {e}",
                        started_at=_now(), finished_at=_now(),
                    ),
                )
                return 0  # graceful exit
        # 1. Pick category — UCB1 bandit, with agent override blended in
        category = bandit.choose(agent_override=next_category)
        next_category = None  # reset; agent will set if it wants

        # 2. Search marketplace
        try:
            candidates = mkt.pick_top(
                category=category,
                exclude_ids=seen_listing_ids,
                top_n=1,
            )
        except Exception as e:
            logger.warning("marketplace search failed: %s", e)
            candidates = []
        if not candidates:
            logger.info("iter %d: no candidates in %s — skipping", iter_no, category)
            _persist_iteration(
                spark, conn, catalog,
                IterationRecord(
                    iter_no=iter_no, listing_id="", category=category,
                    status="skipped", summary="no candidates in category",
                    started_at=_now(), finished_at=_now(),
                ),
            )
            time.sleep(args.stagger_seconds)
            continue

        listing = candidates[0]
        seen_listing_ids.add(listing.id)

        # 3. Install
        t0 = time.time()
        record = IterationRecord(
            iter_no=iter_no, listing_id=listing.id, category=category,
            status="running", started_at=_now(),
        )
        with connect() as conn:
            record_iteration_start(conn, iter_no, listing.id)
        _persist_iteration(spark, conn, catalog, record)

        # 4-6. ingest → DLT → MLOps (with retry)
        retry_count = 0
        while retry_count <= args.max_retries:
            try:
                # 4. ingest
                fulfillments = mkt.list_fulfillments(listing.id)
                ingest = ingest_listing(
                    spark, listing, fulfillments, catalog=catalog,
                )
                record.bronze_table = ingest.bronze_table
                logger.info("iter %d: %s", iter_no, ingest.summary)

                # 5. DLT
                dlt = promote_locally(
                    spark, listing.id, ingest.bronze_table, catalog=catalog,
                )
                record.silver_table = dlt.silver_table
                record.gold_table = dlt.gold_table
                logger.info("iter %d: %s", iter_no, dlt.summary)

                # 6. MLOps
                mlops = run_baseline(
                    spark, dlt.silver_table, listing.id, iter_no,
                    catalog=catalog,
                )
                record.mlflow_run_id = mlops.mlflow_run_id
                record.model_name = mlops.model_name
                logger.info(
                    "iter %d: MLOps %s metrics=%s",
                    iter_no, mlops.model_name, mlops.metrics,
                )

                # 6b. Deploy + monitor the baseline. Best-effort:
                # a serving failure is logged but does not fail
                # the iteration (the model is still trained and
                # logged to MLflow).
                if not args.no_serving:
                    from .serving import deploy_and_monitor
                    endpoint_name = (
                        f"m100_endpoint_{listing.id[:24]}_{iter_no}"
                    )
                    # Use the first numeric feature col as the probe input.
                    probe_input = [{"x": float(i)} for i in range(5)]
                    serving = deploy_and_monitor(
                        workspace_client=workspace,
                        model_name=mlops.model_name,
                        endpoint_name=endpoint_name,
                        sample_input=probe_input,
                        n_requests=args.serving_probe_n,
                    )
                    record.endpoint_name = serving.endpoint_name
                    record.endpoint_p95_ms = round(serving.p95_ms, 3)
                    record.endpoint_drift = round(serving.drift_score, 4)
                    logger.info(
                        "iter %d: serving p95=%.1fms drift=%.3f err=%.1f%%",
                        iter_no, serving.p95_ms, serving.drift_score,
                        serving.error_rate * 100,
                    )

                # 7. Agent
                # recent_history = the last 5 iterations, so the
                # agent has short-term context without doing a tool call.
                recent_history = [
                    {
                        "iter_no": m["iter_no"],
                        "category": m["category"],
                        "summary": m["summary"],
                        "quality_score": m["quality_score"],
                    }
                    for m in (history.meta[-5:] if history.meta else [])
                ]
                agent_result = agent.evaluate(
                    iter_no=iter_no,
                    listing_id=listing.id,
                    silver_table=dlt.silver_table,
                    gold_table=dlt.gold_table,
                    mlflow_run_id=mlops.mlflow_run_id,
                    dlt_pipeline_id=f"m100_dlt_{listing.id}",
                    current_category=category,
                    recent_history=recent_history,
                )
                record.quality_score = agent_result.quality_score
                record.next_category = agent_result.next_category
                record.summary = agent_result.summary
                logger.info(
                    "iter %d: agent score=%.2f retry=%s next=%s",
                    iter_no, agent_result.quality_score, agent_result.retry,
                    agent_result.next_category,
                )

                with connect() as conn:
                    record_agent_call(
                        conn,
                        iter_no=iter_no,
                        listing_id=listing.id,
                        prompt_tokens=agent_result.prompt_tokens,
                        completion_tokens=agent_result.completion_tokens,
                        latency_ms=agent_result.latency_ms,
                        quality_score=agent_result.quality_score,
                        summary=agent_result.summary,
                        raw_response=agent_result.raw_response,
                    )

                # Cost telemetry — record the FM API spend for this
                # iteration. DBU is sampled at the end of the iter
                # (per-iter DBU is hard to attribute, so we use the
                # day's running total as a proxy and let the
                # BudgetGuard see the trend).
                dbu_this_iter = read_dbu_for_iteration(spark, iter_no=iter_no)
                cost_rec = cost_ledger.record(
                    iter_no=iter_no,
                    model=agent.fm_endpoint,
                    prompt_tokens=agent_result.prompt_tokens,
                    completion_tokens=agent_result.completion_tokens,
                    dbu=dbu_this_iter,
                )
                record.cost_usd = round(cost_rec.cost_usd, 6)
                record.dbu = dbu_this_iter
                logger.info(
                    "iter %d: spend $%.4f (cum $%.4f) dbu=%.2f (cum %.2f)",
                    iter_no, cost_rec.cost_usd,
                    cost_ledger.total()[0],
                    dbu_this_iter, sum(r.dbu for r in cost_ledger.records),
                )

                if agent_result.quality_score >= args.quality_threshold:
                    # Accept the iteration
                    next_category = agent_result.next_category
                    record.status = "ok"
                    break
                else:
                    # Below threshold — retry
                    retry_count += 1
                    record.retry_count = retry_count
                    logger.info(
                        "iter %d: quality %.2f < threshold %.2f — retry %d/%d",
                        iter_no, agent_result.quality_score, args.quality_threshold,
                        retry_count, args.max_retries,
                    )
                    if retry_count > args.max_retries:
                        record.status = "skipped"
                        break
            except Exception as e:
                logger.exception("iter %d: iteration failed: %s", iter_no, e)
                record.status = "failed"
                record.summary = f"error: {e}"
                break

        record.duration_seconds = round(time.time() - t0, 1)
        record.finished_at = _now()
        with connect() as conn:
            record_iteration_end(
                conn, iter_no,
                status=record.status,
                quality_score=record.quality_score,
            )
            # Persist the bandit's updated state so the next boot
            # picks up where we left off.
            save_to_lakebase(conn, bandit)
        _persist_iteration(spark, conn, catalog, record)

        # Bandit update — feed the observed quality_score back as
        # the reward. Even retries update (negative signal).
        bandit.update(category, record.quality_score)

        # History index update — add this iteration's summary so
        # future agent calls can query it semantically.
        if record.summary and record.status == "ok":
            history.add_iteration(
                iter_no=iter_no,
                listing_id=record.listing_id,
                category=record.category,
                summary=record.summary,
                quality_score=record.quality_score,
            )

        # Stagger
        logger.info(
            "iter %d: done (status=%s, %.1fs). sleeping %ds.",
            iter_no, record.status, record.duration_seconds, args.stagger_seconds,
        )
        time.sleep(args.stagger_seconds)

    logger.info("driver finished (max_iterations=%d)", args.max_iterations)
    return 0


def _now() -> str:
    """ISO timestamp for the iteration record."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _persist_iteration(spark, conn, catalog: str, record: IterationRecord) -> None:
    """Append the record to the Delta iterations table.

    The Postgres ops log is updated by the caller (different
    code path so the connection can be opened/closed per
    operation).
    """
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.agents")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.agents.iterations (
            iter_no          INT,
            listing_id       STRING,
            category         STRING,
            status           STRING,
            bronze_table     STRING,
            silver_table     STRING,
            gold_table       STRING,
            mlflow_run_id    STRING,
            model_name       STRING,
            quality_score    DOUBLE,
            next_category    STRING,
            summary          STRING,
            retry_count      INT,
            duration_seconds DOUBLE,
            started_at       STRING,
            finished_at      STRING,
            cost_usd         DOUBLE,
            dbu              DOUBLE,
            endpoint_name    STRING,
            endpoint_p95_ms  DOUBLE,
            endpoint_drift   DOUBLE
        )
        USING delta
        PARTITIONED BY (status)
    """)
    row = asdict(record)
    # `partitioned by` columns must not be in the row data
    status = row.pop("status")
    df = spark.createDataFrame([row | {"status": status}])
    df.write.mode("append").saveAsTable(f"{catalog}.agents.iterations")


if __name__ == "__main__":
    sys.exit(main() or 0)
