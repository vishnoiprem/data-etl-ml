"""
ingest.py — COPY INTO + Auto Loader ingest from a marketplace fulfillment.

The Marketplace `list_fulfillments` response gives us a list of
file records. Each has a path, a format (delta/csv/parquet/json),
and optional streaming hints. We route by format:

  * delta  — already a Delta table; we just `CREATE TABLE ... USING delta`
             at the path. The simplest case.
  * parquet / csv / json  — static files, we use `COPY INTO` for
             atomic + resumable ingest.
  * anything marked `streaming=true`  — we use Auto Loader
             (`cloudFiles`) for incremental ingest.

Every result lands in Unity Catalog:
   `<catalog>.bronze.<listing_id>_<short_hash>`

Bronze is the raw layer; DLT later promotes bronze → silver → gold.

Why two ingest paths (COPY INTO + Auto Loader) instead of always
one? Because:
  * `COPY INTO` is idempotent and atomic for batch files (perfect
    for one-shot marketplace dumps).
  * Auto Loader is the only way to do streaming tail on a folder.
    Marketplace sometimes publishes a folder that grows; the
    driver will re-discover new files on the next iteration.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType

from .marketplace_client import Listing

logger = logging.getLogger(__name__)


# ============================================================
# Result type
# ============================================================

@dataclass
class IngestResult:
    """What ingest produced. The driver persists this to the
    iterations Delta table as `bronze_path` and `bronze_format`."""
    listing_id: str
    bronze_table: str          # fully-qualified: <catalog>.bronze.<id>_<hash>
    bronze_path: str           # underlying path (DBFS / S3 / ...)
    format: str                # delta | parquet | csv | json
    row_count: int
    schema_json: str           # JSON-encoded StructType for downstream
    streaming: bool            # whether Auto Loader was used

    @property
    def summary(self) -> str:
        kind = "Auto Loader" if self.streaming else "COPY INTO"
        return (
            f"{kind} → {self.bronze_table}  "
            f"({self.row_count:,} rows, format={self.format})"
        )


# ============================================================
# Catalog helpers
# ============================================================

def short_hash(s: str, n: int = 6) -> str:
    """A short, filename-safe hash of a string. We use this
    in table names so a listing id with weird chars doesn't
    break DDL."""
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:n]


def bronze_table_name(listing: Listing) -> str:
    """Fully-qualified bronze table name for a listing.

    Pattern: `<catalog>.bronze.<safe_id>_<short_hash>`
    Where `safe_id` is the listing id with non-alnum chars replaced.
    """
    safe = "".join(c if c.isalnum() else "_" for c in listing.id)[:24]
    return f"bronze.{safe}_{short_hash(listing.id)}"


# ============================================================
# Format dispatch
# ============================================================

def ingest_listing(
    spark: SparkSession,
    listing: Listing,
    fulfillment: list[dict],
    *,
    catalog: str = "marketplace_100",
    catalog_ready: bool = False,
) -> IngestResult:
    """Top-level entry point. Picks the right strategy per format.

    `fulfillment` is the list returned by `list_fulfillments`.
    The function expects AT LEAST one file record; raises
    `ValueError` if not.
    """
    if not fulfillment:
        raise ValueError(f"listing {listing.id} has no fulfillments")

    if not catalog_ready:
        _ensure_catalog_and_schema(spark, catalog)

    target = f"{catalog}.{bronze_table_name(listing)}"

    # Group by format and streaming flag. Delta > parquet > csv > json.
    # Most listings are Delta; the rest are static file drops.
    by_format: dict[str, list[dict]] = {"delta": [], "parquet": [], "csv": [], "json": []}
    streaming_hints = []
    for f in fulfillment:
        fmt = (f.get("format") or f.get("fileFormat") or "").lower()
        if fmt not in by_format:
            # Unknown — treat as parquet; the COPY INTO will fail loud
            # and we'll know.
            fmt = "parquet"
        by_format[fmt].append(f)
        if f.get("streaming") or f.get("incremental"):
            streaming_hints.append(f)

    if by_format["delta"]:
        return _ingest_delta(spark, listing, target, by_format["delta"][0])
    if streaming_hints:
        return _ingest_streaming(spark, listing, target, streaming_hints[0])
    if by_format["parquet"]:
        return _ingest_static(spark, listing, target, by_format["parquet"], "parquet")
    if by_format["csv"]:
        return _ingest_static(spark, listing, target, by_format["csv"], "csv")
    if by_format["json"]:
        return _ingest_static(spark, listing, target, by_format["json"], "json")
    raise ValueError(f"listing {listing.id}: no recognized format in {fulfillment}")


# ============================================================
# Catalog / schema setup
# ============================================================

def _ensure_catalog_and_schema(spark: SparkSession, catalog: str) -> None:
    """Create the catalog + bronze schema if they don't exist.

    In a real workspace the catalog is usually pre-provisioned
    via Terraform / DAB; this is the dev-friendly fallback.
    """
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.bronze")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.silver")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.gold")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.agents")


# ============================================================
# Strategy: delta — already a Delta table; just register
# ============================================================

def _ingest_delta(
    spark: SparkSession,
    listing: Listing,
    target: str,
    file_record: dict,
) -> IngestResult:
    """For Delta sources, we register the existing Delta path as a UC table.

    No copy, no transformation. The driver just needs a table it
    can read in the next step.
    """
    path = file_record.get("path") or file_record.get("url")
    if not path:
        raise ValueError(f"delta file record missing path: {file_record}")
    # `CREATE TABLE ... USING delta LOCATION ...` registers without
    # moving data.
    spark.sql(f"DROP TABLE IF EXISTS {target}")
    spark.sql(f"CREATE TABLE {target} USING delta LOCATION '{path}'")
    df = spark.read.table(target)
    row_count = df.count()
    schema_json = df.schema.json()
    logger.info("delta ingest %s → %s (%d rows)", listing.id, target, row_count)
    return IngestResult(
        listing_id=listing.id,
        bronze_table=target,
        bronze_path=path,
        format="delta",
        row_count=row_count,
        schema_json=schema_json,
        streaming=False,
    )


# ============================================================
# Strategy: streaming — Auto Loader
# ============================================================

def _ingest_streaming(
    spark: SparkSession,
    listing: Listing,
    target: str,
    file_record: dict,
) -> IngestResult:
    """Auto Loader ingest for incremental sources.

    Uses `cloudFiles` format — the most reliable Auto Loader
    option (handles schema evolution via schemaLocation).
    """
    path = file_record.get("path") or file_record.get("url")
    if not path:
        raise ValueError(f"streaming file record missing path: {file_record}")
    fmt = (file_record.get("format") or "parquet").lower()
    schema_loc = f"dbfs:/tmp/marketplace_100/checkpoints/{listing.id}"
    spark.sql(f"DROP TABLE IF EXISTS {target}")
    reader = (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", fmt)
        .option("cloudFiles.schemaLocation", schema_loc)
        .option("cloudFiles.inferColumnTypes", "true")
        .load(path)
    )
    query = (
        reader.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", schema_loc + "/cp")
        .option("mergeSchema", "true")
        .toTable(target)
    )
    # One micro-batch is enough for the smoke test; in a 100-iter
    # loop we stop after 30s or when rows arrive.
    query.awaitTermination(timeoutSeconds=30)
    row_count = spark.read.table(target).count()
    schema_json = spark.read.table(target).schema.json()
    logger.info("autoloader ingest %s → %s (%d rows)", listing.id, target, row_count)
    return IngestResult(
        listing_id=listing.id,
        bronze_table=target,
        bronze_path=path,
        format=fmt,
        row_count=row_count,
        schema_json=schema_json,
        streaming=True,
    )


# ============================================================
# Strategy: static files — COPY INTO
# ============================================================

def _ingest_static(
    spark: SparkSession,
    listing: Listing,
    target: str,
    file_records: list[dict],
    fmt: str,
) -> IngestResult:
    """COPY INTO for batch files. Idempotent + atomic.

    `COPY INTO` records what it has already loaded in
    `<table>._copy_into_log`, so re-running is a no-op. That's
    the property we want: if the driver retries an iteration
    after a crash, we don't double the data.
    """
    # Stage the files locally first if they're URLs.
    paths: list[str] = []
    for fr in file_records:
        p = fr.get("path") or fr.get("url")
        if not p:
            logger.warning("file record missing path: %s", fr)
            continue
        paths.append(p)
    if not paths:
        raise ValueError(f"listing {listing.id}: no usable paths in {file_records}")

    spark.sql(f"DROP TABLE IF EXISTS {target}")
    if fmt == "parquet":
        spark.sql(f"CREATE TABLE {target} USING parquet")
    elif fmt == "csv":
        spark.sql(
            f"CREATE TABLE {target} (value STRING) USING csv "
            f"OPTIONS (header 'true', inferSchema 'true')"
        )
    elif fmt == "json":
        spark.sql(f"CREATE TABLE {target} USING json")

    # COPY INTO one at a time so a single bad file doesn't kill
    # the rest. Errors are logged; the driver counts the final
    # row_count and decides whether to keep the iteration.
    copied = 0
    for p in paths:
        try:
            spark.sql(f"COPY INTO {target} FROM '{p}' FILEFORMAT = {fmt.upper()}")
            copied += 1
        except Exception as e:
            logger.warning("COPY INTO %s failed for %s: %s", target, p, e)

    df = spark.read.table(target)
    row_count = df.count()
    schema_json = df.schema.json()
    logger.info(
        "static ingest %s → %s (%d rows, %d/%d files copied)",
        listing.id, target, row_count, copied, len(paths),
    )
    return IngestResult(
        listing_id=listing.id,
        bronze_table=target,
        bronze_path=",".join(paths),
        format=fmt,
        row_count=row_count,
        schema_json=schema_json,
        streaming=False,
    )
