import os
import shutil
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

OUT = "/tmp/nbt3k"
shutil.rmtree(OUT, ignore_errors=True)

print("=== ReadFromCsv under Prism, PerKey count ===")
try:
    with beam.Pipeline(runner="DirectRunner") as p:
        rows = p | "R" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
        print("  element_type:", rows.element_type)
        n = rows | "N" >> beam.combiners.Count.PerKey()
        n | "W" >> beam.io.WriteToText(OUT + "/csvcount", num_shards=1, shard_name_template="")
    print("  count:", open(OUT + "/csvcount").read().strip())
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {str(exc)[:300]}")

print()
print("=== ReadFromJson under Prism, PerKey count ===")
try:
    with beam.Pipeline(runner="DirectRunner") as p:
        rows = p | "R" >> beam.io.ReadFromJson("./sample_data/events.ndjson")
        n = rows | "N" >> beam.combiners.Count.PerKey()
        n | "W" >> beam.io.WriteToText(OUT + "/jsoncount", num_shards=1, shard_name_template="")
    print("  count:", open(OUT + "/jsoncount").read().strip())
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {str(exc)[:300]}")
