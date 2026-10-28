import os
import shutil
import apache_beam as beam

OUT = "/tmp/nbt3l"
shutil.rmtree(OUT, ignore_errors=True)

print("=== ReadFromCsv under Prism, Count() ===")
try:
    with beam.Pipeline(runner="DirectRunner") as p:
        rows = p | "R" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
        n = rows | "N" >> beam.combiners.Count()
        n | "W" >> beam.io.WriteToText(OUT + "/csvcount", num_shards=1, shard_name_template="")
    print("  csv count:", open(OUT + "/csvcount").read().strip())
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {str(exc)[:200]}")

print()
print("=== ReadFromJson under Prism, Count() ===")
try:
    with beam.Pipeline(runner="DirectRunner") as p:
        rows = p | "R" >> beam.io.ReadFromJson("./sample_data/events.ndjson")
        n = rows | "N" >> beam.combiners.Count()
        n | "W" >> beam.io.WriteToText(OUT + "/jsoncount", num_shards=1, shard_name_template="")
    print("  json count:", open(OUT + "/jsoncount").read().strip())
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {str(exc)[:200]}")

print()
print("=== ReadFromCsv under Prism, first 2 rows ===")
try:
    with beam.Pipeline(runner="DirectRunner") as p:
        rows = p | "R" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
        two = rows | "Take" >> beam.combiners.Sample(2) if hasattr(beam.combiners, "Sample") else rows
        two | "W" >> beam.io.WriteToText(OUT + "/csv2", num_shards=1, shard_name_template="")
    print(open(OUT + "/csv2").read()[:400])
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {str(exc)[:200]}")
