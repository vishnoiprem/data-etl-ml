"""
SCB AML Platform — Pipeline Orchestrator
Simulates Oozie / Airflow daily pipeline schedule.

Daily schedule (mirroring architecture diagram):
  00:00  Sqoop Extract Starts
  02:00  ODS Load Complete
  03:00  CDM Transform Complete
  05:00  Spark Jobs Complete (Entity Res + Aggregation + Features + Screening)
  06:00  AML Screening + Alert Generation
  07:00  Lucid Search Index Refresh
  08:00  Analysts Start Work (data ready)

Each step runs sequentially and passes state via files.
Run: python pipeline_orchestrator.py [--date YYYYMMDD]
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

BASE = Path(__file__).resolve().parent.parent


def step(name: str, simulated_time: str):
    """Print step header."""
    logger.info(f"\n{'='*60}")
    logger.info(f"PIPELINE STEP: {name}")
    logger.info(f"Simulated wall time: {simulated_time}")
    logger.info(f"{'='*60}")


def run_pipeline(run_date: str = None):
    start = datetime.utcnow()
    if run_date is None:
        run_date = start.strftime("%Y%m%d")

    logger.info(f"""
╔══════════════════════════════════════════════════════════╗
║   SCB AML Platform — Daily Pipeline Run                 ║
║   Date  : {run_date}                                    ║
║   Author: Prem Vishnoi, Big Data Consultant             ║
║   Scope : 15 Countries, T+1 SLA                         ║
╚══════════════════════════════════════════════════════════╝
""")

    # ── STEP 0: Generate dummy data (first run only)
    dummy_manifest = BASE / "data" / "dummy" / "manifest.json"
    if not dummy_manifest.exists():
        step("STEP 0: Generate Dummy Data", "Pre-requisite")
        from scb_aml_platform.data.dummy.generate_dummy_data import main as gen_data
        gen_data()
    else:
        logger.info("Dummy data already generated. Skipping.")

    # ── STEP 1: Sqoop Ingestion (00:00 → 02:00)
    step("STEP 1: Sqoop Batch Ingestion (ODS Load)", "00:00 → 02:00")
    from scb_aml_platform.ingestion.sqoop_ingest import run_all as sqoop_run
    sqoop_run(run_date)
    logger.success("ODS Load Complete [02:00 SLA MET]")

    # ── STEP 2: Hive Simulator Load (02:00 → 03:00)
    step("STEP 2: Load ODS into Hive Simulator", "02:00 → 03:00")
    from scb_aml_platform.hive.scripts.hive_simulator import load_ods_tables, get_table_info
    load_ods_tables()
    info = get_table_info()
    logger.success(f"Hive tables loaded: {list(info.keys())}")
    logger.success("CDM Transform Complete [03:00 SLA MET]")

    # ── STEP 3: Spark Job 1 — Entity Resolution (03:00 → 05:00)
    step("STEP 3: Spark Job 1 — Entity Resolution", "03:00 → 05:00")
    from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import run as er_run
    entity_master = er_run()
    logger.success(f"Entity master: {len(entity_master):,} golden entities")

    # ── STEP 4: Spark Job 2 — Transaction Aggregation
    step("STEP 4: Spark Job 2 — Transaction Aggregation", "03:30 → 04:00")
    from scb_aml_platform.spark.aggregation.job2_transaction_aggregation import run as agg_run
    agg_run()

    # ── STEP 5: Spark Job 3 — Feature Engineering
    step("STEP 5: Spark Job 3 — Feature Engineering (200+ features)", "04:00 → 05:00")
    from scb_aml_platform.spark.feature_engineering.job3_feature_engineering import run as fe_run
    fe_run()

    # ── STEP 6: Spark Job 4 — Sanctions/PEP Screening
    step("STEP 6: Spark Job 4 — Sanctions & PEP Screening", "04:30 → 05:00")
    from scb_aml_platform.spark.screening.job4_sanctions_pep_screening import run as screen_run
    screen_run()
    logger.success("All Spark Jobs Complete [05:00 SLA MET]")

    # ── STEP 7: Risk Scoring Engine (05:00 → 06:00)
    step("STEP 7: Risk Scoring Engine (CRS / TRS / NRS)", "05:00 → 06:00")
    from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import run as risk_run
    risk_run()

    # ── STEP 8: Rules Engine + Alert Generation (06:00)
    step("STEP 8: Rules Engine + Alert Generation", "06:00")
    from scb_aml_platform.aml_engine.rules.rules_engine import run as rules_run
    rules_run()
    from scb_aml_platform.aml_engine.alert_generation.alert_generator import run as alert_run
    alert_run()
    logger.success("AML Screening + Alert Gen Complete [06:00 SLA MET]")

    # ── STEP 9: Lucid Search Index Refresh (07:00)
    step("STEP 9: Lucid Search Index Refresh (Elasticsearch)", "07:00")
    from scb_aml_platform.elasticsearch.scripts.es_index_manager import run as es_run
    es_run()
    logger.success("Lucid Search Index Refresh Complete [07:00 SLA MET]")

    # ── PIPELINE COMPLETE
    elapsed = (datetime.utcnow() - start).total_seconds()
    logger.info(f"""
╔══════════════════════════════════════════════════════════╗
║   PIPELINE COMPLETE — T+1 SLA                           ║
║   Run date  : {run_date}                                ║
║   Elapsed   : {elapsed:.1f}s                                   ║
║   Status    : 08:00 — Analysts can start work           ║
╚══════════════════════════════════════════════════════════╝
""")

    # Print output file locations
    output_dir = BASE / "output"
    logger.info("\nOutput files:")
    for f in sorted(output_dir.rglob("*.*")):
        logger.info(f"  {f.relative_to(BASE)}")

    processed_dir = BASE / "data" / "processed"
    logger.info("\nProcessed data files:")
    for f in sorted(processed_dir.glob("*.parquet")):
        logger.info(f"  {f.relative_to(BASE)}")

    return run_date


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SCB AML Platform Pipeline Orchestrator")
    parser.add_argument("--date", type=str, default=None,
                        help="Run date YYYYMMDD (default: today)")
    args = parser.parse_args()
    run_pipeline(args.date)
