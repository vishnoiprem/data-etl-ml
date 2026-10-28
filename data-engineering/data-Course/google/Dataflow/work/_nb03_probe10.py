import os
import shutil
import csv
import json
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

OPTS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
OUT = "/tmp/nbt3j"
shutil.rmtree(OUT, ignore_errors=True)

print("=== ReadFromCsv under BundleBasedDirectRunner ===")
try:
    with beam.Pipeline(options=OPTS) as p:
        rows = p | "R" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
        print("  element_type:", rows.element_type)
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {str(exc)[:160]}")

print()
print("=== ReadFromCsv under Prism (DirectRunner) ===")
try:
    with beam.Pipeline(runner="DirectRunner") as p:
        rows = p | "R" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
        print("  element_type:", rows.element_type)
        n = rows | "N" >> beam.combiners.Count()
        n | "W" >> beam.io.WriteToText(OUT + "/csvcount", num_shards=1, shard_name_template="")
    print("  count:", open(OUT + "/csvcount").read().strip())
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {str(exc)[:200]}")

print()
print("=== ReadFromJson under BundleBasedDirectRunner ===")
try:
    with beam.Pipeline(options=OPTS) as p:
        rows = p | "R" >> beam.io.ReadFromJson("./sample_data/events.ndjson")
        print("  element_type:", rows.element_type)
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {str(exc)[:160]}")

print()
print("=== ReadFromJson under Prism ===")
try:
    with beam.Pipeline(runner="DirectRunner") as p:
        rows = p | "R" >> beam.io.ReadFromJson("./sample_data/events.ndjson")
        print("  element_type:", rows.element_type)
        n = rows | "N" >> beam.combiners.Count()
        n | "W" >> beam.io.WriteToText(OUT + "/jsoncount", num_shards=1, shard_name_template="")
    print("  count:", open(OUT + "/jsoncount").read().strip())
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {str(exc)[:200]}")
