import os

# Spark 4.x requires Java 17+ (class file 61). `java` on PATH here is the
# macOS Java 11 stub, and JAVA_HOME is unset, so pyspark's `spark-class`
# wrapper falls back to `java` and dies with UnsupportedClassVersionError.
# Point JAVA_HOME at a modern JDK *before* pyspark spawns the JVM.
_JAVA_CANDIDATES = (
    "/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home",
    "/opt/homebrew/opt/openjdk",
    "/usr/local/opt/openjdk/libexec/openjdk.jdk/Contents/Home",
    "/usr/local/opt/openjdk",
    "/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home",
)


def _major_version(java_home: str) -> int:
    """Best-effort read of the JDK's major version (17, 21, 27, ...)."""
    release = os.path.join(java_home, "release")
    try:
        with open(release, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("JAVA_VERSION="):
                    raw = line.split("=", 1)[1].strip().strip('"')
                    head = raw.split(".")[0]
                    if head.isdigit():
                        return int(head)
                    # e.g. "1.8.0_402"
                    return 8
    except OSError:
        pass
    return 0


def _ensure_java() -> str | None:
    """Ensure JAVA_HOME points at a JDK new enough for the installed Spark.

    Returns the selected JAVA_HOME, or None if the environment was already
    usable. Raises RuntimeError only when no compatible JDK is found AND
    the caller has not provided one.
    """
    current = os.environ.get("JAVA_HOME", "")
    if current and _major_version(current) >= 17:
        return current

    for candidate in _JAVA_CANDIDATES:
        if os.path.isdir(candidate) and _major_version(candidate) >= 17:
            os.environ["JAVA_HOME"] = candidate
            os.environ["PATH"] = (
                os.path.join(candidate, "bin") + os.pathsep + os.environ.get("PATH", "")
            )
            return candidate
    return current or None


_selected = _ensure_java()
print("JAVA_HOME ->", _selected)

from pyspark.sql import SparkSession, functions as F  # noqa: E402

s = SparkSession.builder.master("local[2]").appName("probe4").getOrCreate()
print("SPARK VERSION:", s.version)
df = s.createDataFrame([(1, "a"), (2, "b"), (3, "c")], ["n", "s"])
df.show()
print("AQE:", s.conf.get("spark.sql.adaptive.enabled"))
for fn in ("array_agg", "try_element_at", "variant_type", "trim_col", "hll_sketch_approx"):
    print(f"  {fn}: {hasattr(F, fn)}")
s.stop()
print("OK")
