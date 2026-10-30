"""
Problem 01: An Airflow DAG for a daily partitioned load.

Meta flavor: "Sketch the orchestration for this pipeline. What happens when it
fails at 3am?"

NOTE: Airflow is NOT installed in this venv, so this file does not execute a
scheduler. The import is guarded and the module still imports cleanly so the
code stays syntax-checked. The DAG shape is what gets discussed in an
interview, not a running scheduler.

How to Think — the five things an interviewer is listening for:
  1. IDEMPOTENT TASKS. Every task takes the logical date as a parameter and
     overwrites its own partition. Retrying task 3 must not duplicate data.
     `{{ ds }}` (the logical date), never `date.today()` — using wall-clock time
     makes a backfill silently process today's data for every historical run.
  2. NO WORK IN THE DAG FILE. The DAG file is parsed every ~30s by the
     scheduler. A query or an API call at module level runs hundreds of times a
     day and will take the scheduler down.
  3. SENSORS/DEPENDENCIES over guessing. Wait for upstream data to land rather
     than scheduling an hour later and hoping.
  4. RETRIES WITH BACKOFF, and an SLA so a late run pages someone. Retries
     without backoff hammer a service that is already failing.
  5. DATA QUALITY AS A TASK that can FAIL the DAG. A pipeline that cheerfully
     publishes an empty table is worse than one that breaks loudly.

catchup=False is set deliberately: with catchup=True, deploying this DAG with a
start_date months back immediately schedules every missed interval at once and
floods the cluster. Backfills should be explicit (see 09/03), not a deploy
side effect.
"""

DAG_SOURCE = '''
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

default_args = {
    "owner": "data-eng",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,      # 5m, 10m, 20m — do not hammer
    "max_retry_delay": timedelta(minutes=30),
    "sla": timedelta(hours=2),              # page if the run is late
    "depends_on_past": False,
}

with DAG(
    dag_id="marketplace_orders_daily",
    start_date=datetime(2026, 1, 1),
    schedule="0 2 * * *",
    catchup=False,                # never backfill implicitly on deploy
    max_active_runs=1,            # one logical date at a time
    default_args=default_args,
    tags=["marketplace", "daily"],
) as dag:

    # 1. Wait for upstream rather than guessing a safe hour.
    wait_upstream = ExternalTaskSensor(
        task_id="wait_for_raw_orders",
        external_dag_id="raw_ingest",
        external_task_id="land_orders",
        timeout=60 * 60,
        poke_interval=120,
        mode="reschedule",        # free the worker slot while waiting
    )

    # 2. Transform ONE partition, keyed on the logical date.
    def transform(ds, **_):
        """Idempotent: overwrites exactly the {ds} partition."""
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
        (spark.table("raw.orders")
             .where(f"order_date = '{ds}'")
             .write.mode("overwrite")
             .partitionBy("order_date")
             .saveAsTable("curated.fact_order"))

    build = PythonOperator(task_id="build_fact_order", python_callable=transform)

    # 3. Quality gate that can FAIL the run.
    def assert_not_empty(ds, **_):
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        n = spark.table("curated.fact_order").where(f"order_date = '{ds}'").count()
        if n == 0:
            raise ValueError(f"fact_order partition {ds} is empty - refusing to publish")

    check = PythonOperator(task_id="quality_gate", python_callable=assert_not_empty)

    wait_upstream >> build >> check
'''

try:
    import airflow  # noqa: F401
    HAS_AIRFLOW = True
except ImportError:
    HAS_AIRFLOW = False

if __name__ == "__main__":
    # Always verify the DAG source is at least valid Python, even with no Airflow.
    compile(DAG_SOURCE, "marketplace_orders_daily.py", "exec")
    print("[PASS] DAG source compiles as valid Python")

    if HAS_AIRFLOW:
        ns = {}
        exec(compile(DAG_SOURCE, "dag.py", "exec"), ns)
        dag = ns["dag"]
        assert dag.dag_id == "marketplace_orders_daily"
        assert not dag.catchup, "catchup must be False"
        print(f"[PASS] DAG built: {len(dag.tasks)} tasks, catchup={dag.catchup}")
    else:
        print("[SKIP] Airflow not installed — DAG not instantiated. "
              "Install with: pip install apache-airflow")

# ---- MySQL way ----------------------------------------------------------
# Same five rules apply; the per-partition unit of work for a MySQL target is
# DELETE + INSERT in a single transaction (the MySQL equivalent of Spark's
# dynamic partition overwrite).
#
# CREATE TABLE + sample data:
#   CREATE TABLE raw_orders (
#       order_id     INT PRIMARY KEY,
#       buyer_id     INT, seller_id INT,
#       order_date   DATE NOT NULL,
#       gross_amount DECIMAL(10,2),
#       status       VARCHAR(20),
#       KEY idx_orders_date (order_date)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   -- (sample inserts omitted for brevity; same shape as 09/02 example)
#
# Idempotent per-date transform (the unit of work):
#   DELIMITER $$
#   CREATE PROCEDURE build_fact_order_for_date(IN p_ds DATE)
#   BEGIN
#       START TRANSACTION;
#       DELETE FROM fact_order WHERE order_date = p_ds;
#       INSERT INTO fact_order (order_id, buyer_id, seller_id, order_date,
#                               gross_amount, status)
#       SELECT order_id, buyer_id, seller_id, order_date, gross_amount, status
#       FROM raw_orders WHERE order_date = p_ds;
#       COMMIT;
#   END$$
#   DELIMITER ;
#
# Quality gate stored procedure (FAIL the run, not silent zero):
#   DELIMITER $$
#   CREATE PROCEDURE assert_not_empty(IN p_ds DATE)
#   BEGIN
#       DECLARE n INT;
#       SELECT COUNT(*) INTO n FROM fact_order WHERE order_date = p_ds;
#       IF n = 0 THEN
#           SIGNAL SQLSTATE '45000'
#             SET MESSAGE_TEXT = 'fact_order partition is empty';
#       END IF;
#   END$$
#   DELIMITER ;
#
# Airflow orchestration (same shape, MySQL calls instead of Spark):
#   from airflow.operators.mysql import MySqlOperator
#
#   build = MySqlOperator(
#       task_id="build_fact_order",
#       sql="CALL build_fact_order_for_date('{{ ds }}')",
#       mysql_conn_id="warehouse",
#   )
#   check = MySqlOperator(
#       task_id="quality_gate",
#       sql="CALL assert_not_empty('{{ ds }}')",
#       mysql_conn_id="warehouse",
#   )
#   wait_upstream >> build >> check
#
# Same five rules:
#   1. IDEMPOTENT — proc overwrites exactly the {{ ds }} partition.
#   2. NO WORK IN THE DAG FILE — connections / procs live in the DB.
#   3. SENSORS over guessing — ExternalTaskSensor on upstream.
#   4. RETRIES WITH BACKOFF + SLA.
#   5. DATA QUALITY AS A TASK that can FAIL the DAG.
