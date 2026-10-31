"""Shared runtime plumbing for the Spark learning labs.

Every script in this tree is meant to be runnable from a clean checkout with
no manual setup. That means two things have to be solved once, centrally:

1. **The JVM.** Spark 4.x is compiled for Java 17+ (class file version 61).
   Many developer machines still have an older JDK as the system default, and
   ``JAVA_HOME`` is frequently unset. PySpark's ``spark-class`` wrapper falls
   back to whatever ``java`` is on ``PATH`` and dies with an opaque
   ``UnsupportedClassVersionError`` deep in the JVM startup. :func:`ensure_java`
   finds a compatible JDK and pins it *before* the gateway is spawned.

2. **Session configuration.** The defaults that make Spark fast (AQE,
   sensible shuffle partition counts, ANSI mode) are opt-in in a stock
   session. :func:`build_session` turns them on so that the examples
   demonstrate production behaviour rather than toy behaviour.

The functions here are deliberately dependency-free apart from PySpark
itself, so importing this module is cheap.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any

__all__ = [
    "LAB_ROOT",
    "DATA_DIR",
    "OUTPUT_DIR",
    "build_session",
    "ensure_java",
    "read_csv",
    "write_parquet",
    "salting_salt_count",
]

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

#: Root of the ``learning/Spark`` tree. Everything else is relative to this,
#: so the labs run identically regardless of the caller's working directory.
LAB_ROOT = Path(__file__).resolve().parent.parent

#: Where generated fixture data lives.
DATA_DIR = LAB_ROOT / "data"

#: Where lab outputs are written. Git-ignored.
OUTPUT_DIR = LAB_ROOT / "output"


# --------------------------------------------------------------------------
# JVM bootstrap
# --------------------------------------------------------------------------

#: JDKs to try, in order of preference, when the current ``JAVA_HOME`` is
#: missing or too old. Covers Homebrew (Apple Silicon + Intel), the
#: official Temurin installer, and Amazon Corretto.
_JAVA_CANDIDATES: tuple[str, ...] = (
    "/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home",
    "/opt/homebrew/opt/openjdk",
    "/usr/local/opt/openjdk/libexec/openjdk.jdk/Contents/Home",
    "/usr/local/opt/openjdk",
    "/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home",
    "/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home",
    "/Library/Java/JavaVirtualMachines/corretto-21.jdk/Contents/Home",
    "/usr/lib/jvm/java-21-openjdk-amd64",
    "/usr/lib/jvm/java-17-openjdk-amd64",
)

#: Minimum Java major version for Spark 4.x.
_MIN_JAVA_MAJOR = 17


def _java_major_version(java_home: str) -> int:
    """Return the major version of the JDK at *java_home*, or ``0``.

    Reads the JDK's ``release`` file rather than shelling out to
    ``java -version``: spawning a JVM just to read a version number is
    slow, and the ``release`` file has been part of every JDK since 9.
    """
    release = os.path.join(java_home, "release")
    try:
        with open(release, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("JAVA_VERSION="):
                    raw = line.split("=", 1)[1].strip().strip('"')
                    head = raw.split(".")[0]
                    if head.isdigit():
                        return int(head)
                    # Legacy 1.8.0_x form.
                    return 8
    except OSError:
        return 0
    return 0


def ensure_java(minimum: int = _MIN_JAVA_MAJOR) -> str | None:
    """Make sure ``JAVA_HOME`` points at a JDK of at least *minimum*.

    Returns the selected ``JAVA_HOME``, or ``None`` if no suitable JDK was
    found. In that case Spark will be attempted anyway and will most likely
    fail with a ``LinkageError`` — but we do not raise here, because the
    caller may have already arranged a working JVM through some other
    mechanism (a container, a cluster submission, ``spark-submit`` with a
    pre-configured environment).
    """
    current = os.environ.get("JAVA_HOME", "")
    if current and _java_major_version(current) >= minimum:
        return current

    for candidate in _JAVA_CANDIDATES:
        if os.path.isdir(candidate) and _java_major_version(candidate) >= minimum:
            os.environ["JAVA_HOME"] = candidate
            # `spark-class` prefers $JAVA_HOME/bin/java but some helpers
            # still resolve `java` through PATH.
            os.environ["PATH"] = (
                os.path.join(candidate, "bin") + os.pathsep + os.environ.get("PATH", "")
            )
            return candidate

    return current or None


# --------------------------------------------------------------------------
# Session construction
# --------------------------------------------------------------------------

#: Configuration applied to every session created by :func:`build_session`.
#:
#: These are not arbitrary. Each one has a production rationale:
#:
#: ``spark.sql.adaptive.enabled``
#:     Adaptive Query Execution coalesces shuffle partitions at runtime
#:     based on actual data size. Without it Spark uses
#:     ``spark.sql.shuffle.partitions`` (200 by default) regardless of
#:     whether the data needs 4 partitions or 4000. This is the single
#:     highest-leverage performance setting in Spark 3+.
#:
#: ``spark.sql.adaptive.skewJoin.enabled``
#:     Detects a skewed join key at runtime and splits the offending
#:     partition across several tasks. See the salting lab for the manual
#:     equivalent.
#:
#: ``spark.sql.shuffle.partitions``
#:     200 is Spark's default but is tuned for big clusters. A local laptop
#:     with 8 cores is better served by 16.
#:
#: ``spark.sql.adaptive.coalescePartitions.enabled``
#:     Merges the small partitions AQE would otherwise leave behind after
#:     a shuffle.
#:
#: ``spark.sql.session.timeZone``
#:     Pinning the timezone makes window boundaries and date bucketing
#:     deterministic across machines. Without it a cluster whose workers
#:     sit in different zones silently produces different aggregations.
#:
#: ``spark.sql.ansi.enabled``
#:     ANSI mode makes Spark throw on overflow and invalid casts instead
#:     of silently returning NULL. Silent NULLs in a financial pipeline are
#:     how reconciliation bugs hide for months.
_DEFAULT_CONF: dict[str, str] = {
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.skewJoin.enabled": "true",
    "spark.sql.shuffle.partitions": "16",
    "spark.sql.session.timeZone": "UTC",
    "spark.sql.ansi.enabled": "true",
    # Broadcast joins are only worth it when the hint survives analysis;
    # this threshold is generous on purpose for the labs.
    "spark.sql.autoBroadcastJoinThreshold": "10485760",
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
}


def build_session(
    app_name: str = "sparklab",
    *,
    master: str = "local[*]",
    conf: dict[str, Any] | None = None,
    quiet: bool = True,
) -> "Any":
    """Create (or fetch) a SparkSession configured for the labs.

    Parameters
    ----------
    app_name:
        Shown in the Spark UI.
    master:
        Spark master URL. Defaults to ``local[*]``.
    conf:
        Extra configuration layered on top of :data:`_DEFAULT_CONF`.
    quiet:
        Set the log level to WARN. The default Spark log level is INFO,
        which is genuinely useful while learning — but it drowns the
        actual output of the examples.

    Returns
    -------
    pyspark.sql.SparkSession
    """
    # Imported lazily so that `import sparklab` stays cheap and does not
    # require a working JVM.
    ensure_java()

    from pyspark.sql import SparkSession

    warnings.filterwarnings(
        "ignore",
        message="PySpark does not yet fully support pandas",
        category=FutureWarning,
    )

    builder = (
        SparkSession.builder.appName(app_name)
        .master(master)
        # Use a local warehouse dir so `saveAsTable` and `CREATE TABLE` do
        # not scribble into the user's home directory.
        .config("spark.sql.warehouse.dir", str(OUTPUT_DIR / "warehouse"))
    )
    for key, value in _DEFAULT_CONF.items():
        builder = builder.config(key, value)
    for key, value in (conf or {}).items():
        builder = builder.config(key, str(value))

    session = builder.getOrCreate()
    if quiet:
        session.sparkContext.setLogLevel("WARN")
    return session


# --------------------------------------------------------------------------
# I/O helpers
# --------------------------------------------------------------------------


def read_csv(
    path: str | os.PathLike[str],
    schema: "Any",
    *,
    session: "Any" = None,
    header: bool = True,
) -> "Any":
    """Read a CSV with an explicit schema.

    Always pass a schema. ``inferSchema=True`` samples the file to guess
    column types, which means (a) an extra full pass over the data, and
    (b) a schema that can differ between runs — a column that is an integer
    in one file and a string in the next will change the plan under you.
    Explicit schemas are how production pipelines are written.
    """
    from pyspark.sql import SparkSession

    spark = session or SparkSession.getActiveSession()
    if spark is None:
        spark = build_session()
    return spark.read.schema(schema).option("header", header).csv(str(path))


def write_parquet(df: "Any", path: str | os.PathLike[str], *, mode: str = "overwrite") -> None:
    """Write a DataFrame as Parquet with sane defaults.

    Parquet is the default choice for Spark output: it is columnar, so
    Spark only reads the columns a query touches, and it is self-describing,
    so the schema travels with the data.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    df.write.mode(mode).parquet(str(target))


# --------------------------------------------------------------------------
# Skew helpers
# --------------------------------------------------------------------------


def salting_salt_count(df: "Any", key: str, *, max_salts: int = 64) -> int:
    """Choose a salt count for *key* from the observed skew.

    The textbook answer is "pick 10". The honest answer is to look at the
    data: count the rows per key, find the maximum, and spread that key
    across enough partitions that each partition's slice is a reasonable
    size relative to the rest of the partition.

    The heuristic here targets roughly 4 MB per salted partition, the size
    at which task overhead stops dominating and the shuffle becomes
    throughput-bound rather than latency-bound. It is a starting point to
    be tuned with real data, not a law.
    """
    from pyspark.sql import functions as F

    counts = df.groupBy(key).count()
    stats = counts.agg(
        F.max("count").alias("max_count"),
        F.count(F.lit(1)).alias("n_keys"),
    ).first()
    if stats is None or not stats["max_count"]:
        return 1

    # Assume ~64 bytes per row after serialization as a starting estimate.
    target_rows = (4 * 1024 * 1024) // 64
    salts = max(1, min(max_salts, stats["max_count"] // target_rows + 1))
    return salts
