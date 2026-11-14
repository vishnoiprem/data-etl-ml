"""Report what the shared .env virtualenv provides."""

import sys

print("python", sys.version.split()[0])
print("executable", sys.executable)

for name in (
    "apache_beam",
    "pyspark",
    "pytest",
    "pandas",
    "google.cloud.bigquery",
    "apache_beam.io.gcp.bigquery",
):
    try:
        mod = __import__(name, fromlist=["*"])
        print(f"{name:34s} {getattr(mod, '__version__', 'present')}")
    except Exception as exc:  # noqa: BLE001
        print(f"{name:34s} MISSING ({type(exc).__name__})")
