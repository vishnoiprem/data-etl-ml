"""
SCB AML Platform — Airflow DAG Definition
Mirrors the daily Oozie/Airflow schedule from the architecture.

To use with real Airflow:
  1. pip install apache-airflow
  2. Copy this file to $AIRFLOW_HOME/dags/
  3. airflow db init && airflow webserver & airflow scheduler

DAG schedule: daily at 00:00 SGT (UTC+8 → UTC 16:00 previous day)
"""

from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False
    # Stub classes for local development without Airflow
    class DAG:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass

    class PythonOperator:
        def __init__(self, **k): pass


DEFAULT_ARGS = {
    "owner": "prem.vishnoi",
    "depends_on_past": False,
    "email": ["aml-platform@sc.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=3),
}

# ── Callable functions for each task
def task_sqoop_ingest(**context):
    from scb_aml_platform.ingestion.sqoop_ingest import run_all
    run_date = context["ds_nodash"]
    run_all(run_date)


def task_hive_ods_load(**context):
    from scb_aml_platform.hive.scripts.hive_simulator import load_ods_tables
    load_ods_tables()


def task_spark_entity_resolution(**context):
    from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import run
    run()


def task_spark_txn_aggregation(**context):
    from scb_aml_platform.spark.aggregation.job2_transaction_aggregation import run
    run()


def task_spark_feature_engineering(**context):
    from scb_aml_platform.spark.feature_engineering.job3_feature_engineering import run
    run()


def task_spark_screening(**context):
    from scb_aml_platform.spark.screening.job4_sanctions_pep_screening import run
    run()


def task_risk_scoring(**context):
    from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import run
    run()


def task_rules_engine(**context):
    from scb_aml_platform.aml_engine.rules.rules_engine import run
    run()


def task_alert_generation(**context):
    from scb_aml_platform.aml_engine.alert_generation.alert_generator import run
    run()


def task_lucid_search_refresh(**context):
    from scb_aml_platform.elasticsearch.scripts.es_index_manager import run
    run()


# ── DAG Definition
with DAG(
    dag_id="scb_aml_daily_pipeline",
    description="SCB AML Platform — Daily T+1 Processing Pipeline (15 countries)",
    schedule_interval="0 16 * * *",   # 00:00 SGT = 16:00 UTC prev day
    start_date=datetime(2018, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["aml", "scb", "financial-crime", "compliance"],
) as dag:

    t1_sqoop = PythonOperator(
        task_id="sqoop_batch_ingestion",
        python_callable=task_sqoop_ingest,
        doc="Sqoop incremental import from Oracle/DB2 for all 15 countries",
    )

    t2_hive = PythonOperator(
        task_id="hive_ods_load",
        python_callable=task_hive_ods_load,
        doc="Load raw data into Hive ODS partitions",
    )

    t3_entity = PythonOperator(
        task_id="spark_entity_resolution",
        python_callable=task_spark_entity_resolution,
        doc="Multi-pass entity resolution across 15 countries",
    )

    t4_agg = PythonOperator(
        task_id="spark_txn_aggregation",
        python_callable=task_spark_txn_aggregation,
        doc="Daily/weekly/monthly transaction aggregations",
    )

    t5_features = PythonOperator(
        task_id="spark_feature_engineering",
        python_callable=task_spark_feature_engineering,
        doc="Compute 200+ AML behavioural features per customer",
    )

    t6_screening = PythonOperator(
        task_id="spark_sanctions_screening",
        python_callable=task_spark_screening,
        doc="Fuzzy match vs OFAC/UN/EU and 10 local sanctions lists",
    )

    t7_risk = PythonOperator(
        task_id="risk_scoring_engine",
        python_callable=task_risk_scoring,
        doc="Compute CRS / TRS / NRS composite AML score",
    )

    t8_rules = PythonOperator(
        task_id="rules_based_detection",
        python_callable=task_rules_engine,
        doc="Apply AML rules (CTR, structuring, sanctions, PEP, velocity)",
    )

    t9_alerts = PythonOperator(
        task_id="alert_generation",
        python_callable=task_alert_generation,
        doc="Generate STR/SAR/CTR alerts and regulatory filing queue",
    )

    t10_lucid = PythonOperator(
        task_id="lucid_search_index_refresh",
        python_callable=task_lucid_search_refresh,
        doc="Refresh Elasticsearch indices for Lucid Search",
    )

    # ── Dependencies (mirrors the architecture diagram schedule)
    t1_sqoop >> t2_hive >> [t3_entity, t4_agg]
    t3_entity >> t5_features
    t4_agg >> t5_features
    t5_features >> t6_screening
    t6_screening >> t7_risk
    t7_risk >> t8_rules
    t8_rules >> t9_alerts
    t9_alerts >> t10_lucid
