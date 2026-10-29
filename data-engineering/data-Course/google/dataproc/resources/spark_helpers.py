"""
spark_helpers.py — shared helpers for the Dataproc + PySpark course.

Copy this file into your project (or the notebooks/ directory) and use it
throughout. It provides:

    get_spark()               - a configured SparkSession for local or cluster
    configure_logging()       - consistent log formatting across a job
    log_dataframe_counts()    - row counts at each pipeline stage
    assert_no_nulls()         - fail fast on nulls in required columns
    assert_row_count()        - fail fast on an unexpected row count
    quarantine_invalid()      - persist rejected rows instead of dropping them
    write_to_bigquery()       - BigQuery connector write with sane defaults
    write_parquet_partitioned() - partitioned Parquet with DYNAMIC overwrite
    get_run_date()            - resolve the run date, defaulting to yesterday
    run_job()                 - context manager: timing, run_id, guaranteed stop

Usage:
    from spark_helpers import get_spark, run_job, log_dataframe_counts

    def main():
        with run_job("my-pipeline") as (spark, run_id):
            df = spark.read.parquet("gs://bucket/raw/")
            log_dataframe_counts(df, "raw", logger=LOG)
            df.write.mode("overwrite").parquet("gs://bucket/curated/")

    if __name__ == "__main__":
        main()

Importing this module does NOT require a GCP account or a Spark install.
Every cloud import is guarded, and PySpark is imported lazily inside
get_spark() so the module can be used for pure-Python helper testing.
"""
from __future__ import annotations

import contextlib
import datetime
import logging
import os
import time
import uuid
from typing import Any, Iterable, Iterator, Sequence

# --------------------------------------------------------------------------
# Optional imports — the module must import cleanly without them.
# --------------------------------------------------------------------------

try:  # pragma: no cover - exercised only when PySpark is installed
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql import functions as F

    PYSPARK_AVAILABLE = True
except ImportError:  # pragma: no cover
    DataFrame = Any  # type: ignore[assignment,misc]
    SparkSession = Any  # type: ignore[assignment,misc]
    F = None  # type: ignore[assignment]
    PYSPARK_AVAILABLE = False

try:  # pragma: no cover
    from google.cloud import bigquery

    BIGQUERY_AVAILABLE = True
except ImportError:  # pragma: no cover
    bigquery = None  # type: ignore[assignment]
    BIGQUERY_AVAILABLE = False


log = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Defaults
# --------------------------------------------------------------------------

DEFAULT_APP_NAME = "dataproc-course"
DEFAULT_ENV = os.environ.get("ENV", "dev")
DEFAULT_BROADCAST_THRESHOLD_MB = int(os.environ.get("SPARK_BROADCAST_THRESHOLD_MB", 10))
DEFAULT_MAX_PARTITIONS = int(os.environ.get("SPARK_MAX_PARTITIONS", 200))

# The production Spark defaults this course applies. Each one is
# deliberate; see resources/CHEATSHEET.md for the reasoning.
PRODUCTION_CONFIGS = {
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.skewJoin.enabled": "true",
    "spark.sql.adaptive.localShuffleReader.enabled": "true",
    "spark.sql.session.timeZone": "UTC",
    "spark.sql.sources.partitionOverwriteMode": "DYNAMIC",
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
    "spark.sql.execution.arrow.pyspark.enabled": "true",
    "spark.sql.parquet.compression.codec": "zstd",
    "spark.sql.adaptive.forceOptimizeSkewedJoin": "false",
}


# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure consistent logging for a course job.

    Replaces any existing handlers so repeated calls in a notebook do
    not duplicate every log line. Returns the root logger.

    Args:
        level: Log level name — "DEBUG", "INFO", "WARNING", "ERROR".

    Returns:
        The configured root logger.
    """
    numeric_level = getattr(logging, str(level).upper(), logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(numeric_level)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Spark's own logging is very noisy at INFO. WARN is the useful level.
    logging.getLogger("py4j").setLevel(logging.WARNING)
    logging.getLogger("org.apache.spark").setLevel(logging.WARN)
    logging.getLogger("org.spark_project").setLevel(logging.WARN)

    log.info("Logging configured at %s", str(level).upper())
    return root


# --------------------------------------------------------------------------
# SparkSession
# --------------------------------------------------------------------------


def get_spark(
    app_name: str = DEFAULT_APP_NAME,
    shuffle_partitions: int | None = None,
    extra_configs: dict[str, str] | None = None,
    local: bool = True,
) -> "SparkSession":
    """Build and return a configured SparkSession.

    In local mode (`local=True`) the session runs on the caller's machine
    using `local[*]` — all available cores. This is how you develop and
    debug the course exercises.

    In cluster mode (`local=False`) the session runs on a Dataproc cluster.
    The driver executes on the master node, so `spark.driver.memory` is
    the master's memory.

    Applies a set of production defaults: adaptive query execution (AQE),
    a broadcast threshold, a shuffle partition count, UTC session timezone,
    and DYNAMIC partition overwrite.

    Args:
        app_name: The Spark application name. Appears in the Dataproc
            console and the Spark UI.
        shuffle_partitions: Value for `spark.sql.shuffle.partitions`.
            Defaults to 200, which is Spark's own default. AQE coalesces
            these at runtime, so this rarely needs changing.
        extra_configs: Additional `key=value` Spark configuration. These
            override the production defaults.
        local: True for `local[*]`, False for cluster mode.

    Returns:
        A configured SparkSession.

    Raises:
        ImportError: If PySpark is not installed.
    """
    if not PYSPARK_AVAILABLE:
        raise ImportError(
            "PySpark is not installed. Run: pip install -r requirements.txt"
        )

    builder = SparkSession.builder.appName(app_name)

    if local:
        builder = builder.master("local[*]")
    else:
        # In cluster mode the SparkSession builder reads the cluster's
        # own configuration (executor counts, memory) from the
        # spark-submit environment. Do not set a master.
        pass

    configs: dict[str, str] = dict(PRODUCTION_CONFIGS)
    configs["spark.sql.shuffle.partitions"] = str(
        shuffle_partitions if shuffle_partitions is not None else DEFAULT_MAX_PARTITIONS
    )
    configs["spark.sql.autoBroadcastJoinThreshold"] = str(
        DEFAULT_BROADCAST_THRESHOLD_MB * 1024 * 1024
    )

    if extra_configs:
        configs.update(extra_configs)

    for key, value in configs.items():
        builder = builder.config(key, value)

    spark = builder.getOrCreate()

    if not local:
        # Surface the cluster's identity in the log. It makes
        # correlating a driver log line with a job in the console
        # trivial.
        try:
            cluster_name = spark.sparkContext.master
            log.info("Spark session up: app=%s master=%s", app_name, cluster_name)
        except Exception:  # pragma: no cover - defensive
            log.info("Spark session up: app=%s", app_name)

    log.info(
        "Spark configured: app=%s local=%s shuffle_partitions=%s aqe=%s",
        app_name,
        local,
        configs["spark.sql.shuffle.partitions"],
        configs["spark.sql.adaptive.enabled"],
    )
    return spark


# --------------------------------------------------------------------------
# Data quality
# --------------------------------------------------------------------------


def log_dataframe_counts(
    df: "DataFrame",
    label: str,
    logger: logging.Logger | None = None,
) -> int:
    """Log the row count of a DataFrame at a pipeline stage.

    Counting forces an action, so this is also a useful progress
    signal during a long job. Use it liberally — a pipeline that logs
    its row counts at every stage tells you exactly where rows
    disappeared.

    Args:
        df: The DataFrame to count.
        label: A short name for the stage, e.g. "after dedup".
        logger: The logger to use. Defaults to this module's logger.

    Returns:
        The row count.
    """
    logger = logger or log
    count = df.count()
    logger.info("STAGE %-30s rows=%d", label, count)
    return count


def assert_no_nulls(
    df: "DataFrame",
    columns: Sequence[str] | str,
) -> None:
    """Raise a ValueError if any of the given columns contains a null.

    Args:
        df: The DataFrame to check.
        columns: A column name, or an iterable of column names.

    Raises:
        ValueError: If any listed column has at least one null.
        KeyError: If a listed column does not exist in the DataFrame.
    """
    if isinstance(columns, str):
        columns = [columns]
    columns = list(columns)
    if not columns:
        return

    existing = set(df.columns)
    missing = [c for c in columns if c not in existing]
    if missing:
        raise KeyError(
            f"Column(s) not present in DataFrame: {missing}. "
            f"Available columns: {sorted(existing)}"
        )

    # Build the null-count expression in one pass so this is a single
    # scan rather than one scan per column.
    null_exprs = [F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)) for c in columns]
    counts = df.agg(*null_exprs).collect()[0]

    violations = {
        col: int(counts[idx] or 0)
        for idx, col in enumerate(columns)
        if int(counts[idx] or 0) > 0
    }
    if violations:
        raise ValueError(f"Null values found in required columns: {violations}")


def assert_row_count(
    df: "DataFrame",
    expected: int,
    tolerance: float = 0.0,
) -> None:
    """Raise a ValueError if the DataFrame's row count is out of range.

    Args:
        df: The DataFrame to count.
        expected: The expected number of rows.
        tolerance: Allowed absolute deviation. 0.0 means an exact
            match; 0.05 means "within 5%".

    Raises:
        ValueError: If the row count falls outside the tolerance band.
    """
    actual = df.count()
    allowed = abs(expected) * float(tolerance)
    if abs(actual - expected) > allowed:
        raise ValueError(
            f"Row count mismatch: expected {expected} "
            f"(+/- {allowed:g}, tolerance {tolerance:g}), got {actual}"
        )


def quarantine_invalid(
    df: "DataFrame",
    valid_df: "DataFrame",
    reason_col: str,
    quarantine_path: str,
    mode: str = "append",
) -> int:
    """Write the rows that failed validation to a quarantine location.

    A row is considered rejected if it is present in `df` but absent
    from `valid_df`. The comparison is by row identity, computed as
    the set difference of the two DataFrames. For large frames, pass
    DataFrames that have already been narrowed to a key column so the
    comparison stays cheap.

    Args:
        df: The full set of rows, before validation.
        valid_df: The subset of rows that passed validation.
        reason_col: The name of the column in `df` that holds the
            rejection reason. The rejected rows are written with this
            column preserved.
        quarantine_path: Where to write the rejected rows. A `gs://`
            path writes Parquet; a local path writes Parquet locally.
        mode: "append" (default) or "overwrite".

    Returns:
        The number of rejected rows written.
    """
    rejected = df.subtract(valid_df)
    count = rejected.count()

    if count == 0:
        log.info("Quarantine: 0 rejected rows for %s", quarantine_path)
        return 0

    log.warning("Quarantine: %d rejected rows written to %s", count, quarantine_path)
    (
        rejected.write.mode(mode)
        .option("partitionOverwriteMode", "DYNAMIC")
        .parquet(quarantine_path)
    )
    return count


# --------------------------------------------------------------------------
# Writers
# --------------------------------------------------------------------------


def write_to_bigquery(
    df: "DataFrame",
    project: str,
    dataset: str,
    table: str,
    mode: str = "WRITE_APPEND",
    temp_bucket: str | None = None,
    partition_field: str | None = None,
) -> None:
    """Write a DataFrame to BigQuery through the Spark connector.

    Applies sane defaults: an explicit temporary GCS bucket for the
    connector's staging files, WRITE_APPEND disposition, and CREATE_IF_NEEDED
    table disposition.

    ⚠️ **WRITE_TRUNCATE without `partition_field` deletes the whole
    table.** If you pass mode="WRITE_TRUNCATE", always pass
    `partition_field` too so only the intended partition is replaced.
    That is what makes a re-run idempotent.

    Args:
        df: The DataFrame to write.
        project: The destination GCP project ID.
        dataset: The destination dataset ID.
        table: The destination table ID.
        mode: "WRITE_APPEND", "WRITE_TRUNCATE", or "WRITE_EMPTY".
        temp_bucket: A GCS bucket for the connector's temporary files.
            Required for WRITE_APPEND and WRITE_TRUNCATE.
        partition_field: The partition column. Required for a
            partition-scoped WRITE_TRUNCATE.

    Raises:
        ValueError: If temp_bucket is missing for a mode that needs it,
            or partition_field is missing for WRITE_TRUNCATE.
    """
    if mode in ("WRITE_APPEND", "WRITE_TRUNCATE") and not temp_bucket:
        raise ValueError(
            f"temp_bucket is required for mode={mode}. The BigQuery connector "
            "writes Parquet to GCS before issuing the LOAD job."
        )

    if mode == "WRITE_TRUNCATE" and not partition_field:
        raise ValueError(
            "partition_field is required for mode=WRITE_TRUNCATE. Without it "
            "the entire table is deleted and recreated. If that is genuinely "
            "what you want, pass partition_field explicitly anyway — make "
            "the intent visible."
        )

    writer = (
        df.write.format("bigquery")
        .option("writeDisposition", mode)
        .option("createDisposition", "CREATE_IF_NEEDED")
    )

    if temp_bucket:
        writer = writer.option("temporaryGcsBucket", temp_bucket)
    if partition_field:
        writer = writer.option("partitionField", partition_field)

    target = f"{project}.{dataset}.{table}"
    log.info(
        "Writing to BigQuery: %s mode=%s partition_field=%s",
        target,
        mode,
        partition_field or "-",
    )
    writer.save(target)
    log.info("BigQuery write complete: %s", target)


def write_parquet_partitioned(
    df: "DataFrame",
    path: str,
    partition_cols: Sequence[str] | str,
) -> None:
    """Write a DataFrame as partitioned Parquet.

    Uses `partitionOverwriteMode=DYNAMIC` so that a re-run replaces only
    the partitions present in the DataFrame and leaves every other
    partition untouched. Without it, `overwrite` wipes the entire
    directory — which is the difference between an idempotent pipeline
    and a data-loss bug.

    Args:
        df: The DataFrame to write.
        path: The output path. `gs://...` for GCS, or a local path.
        partition_cols: A partition column name, or an iterable of them.
    """
    if isinstance(partition_cols, str):
        partition_cols = [partition_cols]
    partition_cols = list(partition_cols)
    if not partition_cols:
        raise ValueError("partition_cols must contain at least one column")

    missing = [c for c in partition_cols if c not in set(df.columns)]
    if missing:
        raise KeyError(
            f"Partition column(s) not present in DataFrame: {missing}. "
            f"Available columns: {sorted(df.columns)}"
        )

    log.info(
        "Writing partitioned Parquet: path=%s partitions=%s rows=%s",
        path,
        partition_cols,
        "computed at write time",
    )
    (
        df.write.mode("overwrite")
        .option("partitionOverwriteMode", "DYNAMIC")
        .partitionBy(*partition_cols)
        .parquet(path)
    )
    log.info("Parquet write complete: %s", path)


# --------------------------------------------------------------------------
# Dates
# --------------------------------------------------------------------------


def get_run_date(arg_default: str | datetime.date | None = None) -> datetime.date:
    """Resolve the run date.

    The run date is the date the pipeline is processing — usually
    yesterday, so that a nightly job picks up the previous day's
    complete data.

    Resolution order:
        1. The `RUN_DATE` environment variable (if set).
        2. The `arg_default` argument.
        3. Yesterday (today minus one day).

    ⚠️ **Never bake `CURRENT_DATE()` into a transform.** Take the date
    as a parameter so that backfills work. This helper is that parameter.

    Args:
        arg_default: A fallback date, as a string ("2026-10-27") or a
            `datetime.date`.

    Returns:
        The resolved run date.

    Raises:
        ValueError: If the resolved value cannot be parsed as a date.
    """
    env_value = os.environ.get("RUN_DATE")
    if env_value:
        return _parse_date(env_value, source="RUN_DATE environment variable")

    if arg_default is not None:
        return _parse_date(arg_default, source="arg_default")

    resolved = datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=1)
    log.info("Run date resolved to %s (yesterday, UTC)", resolved)
    return resolved


def _parse_date(value: str | datetime.date, source: str) -> datetime.date:
    """Parse a date from a string or pass a date through unchanged."""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    try:
        resolved = datetime.date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(
            f"Could not parse '{value}' from {source} as a date. "
            "Use the ISO format YYYY-MM-DD."
        ) from exc
    log.info("Run date resolved to %s (from %s)", resolved, source)
    return resolved


# --------------------------------------------------------------------------
# Job lifecycle
# --------------------------------------------------------------------------


@contextlib.contextmanager
def run_job(
    app_name: str = DEFAULT_APP_NAME,
    local: bool = True,
    shuffle_partitions: int | None = None,
    extra_configs: dict[str, str] | None = None,
    logger: logging.Logger | None = None,
) -> Iterator[tuple["SparkSession", str]]:
    """Context manager that wraps a job with timing, a run ID, and cleanup.

    Yields:
        A tuple of (spark_session, run_id). The run_id is a short unique
        string suitable for labelling outputs and log lines.

    Guarantees:
        - `spark.stop()` is called on exit, even if the body raises.
        - The elapsed time is logged on both success and failure.
        - A unique run_id is generated and logged at the start.

    Usage:
        def main():
            with run_job("retail-etl") as (spark, run_id):
                df = spark.read.parquet("gs://bucket/raw/")
                log_dataframe_counts(df, "raw")
    """
    logger = logger or log
    run_id = f"{datetime.datetime.now(datetime.timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"
    started = time.time()

    logger.info("=" * 70)
    logger.info("JOB START  app=%s run_id=%s local=%s", app_name, run_id, local)
    logger.info("=" * 70)

    spark = get_spark(
        app_name=f"{app_name}-{run_id}",
        shuffle_partitions=shuffle_partitions,
        extra_configs=extra_configs,
        local=local,
    )

    try:
        yield spark, run_id
    except Exception as exc:
        elapsed = time.time() - started
        logger.error("JOB FAILED  app=%s run_id=%s after %.1fs", app_name, run_id, elapsed)
        logger.error("Failure: %s", exc, exc_info=True)
        raise
    else:
        elapsed = time.time() - started
        logger.info("=" * 70)
        logger.info("JOB SUCCESS app=%s run_id=%s in %.1fs", app_name, run_id, elapsed)
        logger.info("=" * 70)
    finally:
        try:
            spark.stop()
            logger.info("Spark stopped for run_id=%s", run_id)
        except Exception:  # pragma: no cover - defensive
            logger.warning("Error while stopping Spark for run_id=%s", run_id)


# --------------------------------------------------------------------------
# Misc
# --------------------------------------------------------------------------


def get_metadata_attribute(name: str, default: str = "") -> str:
    """Read a Dataproc instance attribute from the GCE metadata server.

    This lets a driver discover its own environment — the cluster name,
    the staging bucket, the region — without hardcoding it. The same job
    code then works on a dev cluster and a prod cluster.

    Only reachable from inside a Dataproc cluster. Returns `default`
    everywhere else.

    Args:
        name: The attribute name, e.g. "dataproc-cluster-name".
        default: The value to return if the attribute is unavailable.

    Returns:
        The attribute value, or `default`.
    """
    import urllib.error
    import urllib.request

    url = (
        "http://metadata.google.internal/computeMetadata/v1/instance/attributes/"
        + name
    )
    request = urllib.request.Request(url, headers={"Metadata-Flavor": "Google"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.read().decode("utf-8").strip()
    except (urllib.error.URLError, OSError, TimeoutError):
        return default


def list_files(spark: "SparkSession", path: str) -> list[str]:
    """List the files under a GCS or local path.

    Args:
        spark: The active SparkSession.
        path: The path to list.

    Returns:
        A sorted list of file paths. Empty if the path does not exist.
    """
    jvm = spark.sparkContext._jvm  # type: ignore[attr-defined]
    hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()  # type: ignore[attr-defined]
    filesystem = jvm.org.apache.hadoop.fs.FileSystem.get(hadoop_conf)
    path_obj = jvm.org.apache.hadoop.fs.Path(path)
    if not filesystem.exists(path_obj):
        log.warning("Path does not exist: %s", path)
        return []
    statuses = filesystem.listStatus(path_obj)
    return sorted(str(status.getPath()) for status in statuses)


if __name__ == "__main__":
    configure_logging("INFO")
    print(f"PySpark available: {PYSPARK_AVAILABLE}")
    print(f"BigQuery client available: {BIGQUERY_AVAILABLE}")
    print(f"Run date: {get_run_date()}")
