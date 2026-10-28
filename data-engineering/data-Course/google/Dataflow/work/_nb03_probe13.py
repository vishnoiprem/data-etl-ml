import os
import shutil
import apache_beam as beam

OUT = "/tmp/nbt3m"
shutil.rmtree(OUT, ignore_errors=True)

print("=== ReadFromCsv under Prism: key then Count.PerKey ===")
try:
    with beam.Pipeline(runner="DirectRunner") as p:
        rows = p | "R" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
        keyed = rows | "K" >> beam.Map(lambda r: ("all", 1))
        n = keyed | "N" >> beam.combiners.Count.PerKey()
        n | "W" >> beam.io.WriteToText(OUT + "/csvcount", num_shards=1, shard_name_template="")
    print("  csv count:", open(OUT + "/csvcount").read().strip())
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {str(exc)[:250]}")

print()
print("=== ReadFromJson under Prism: key then Count.PerKey ===")
try:
    with beam.Pipeline(runner="DirectRunner") as p:
        rows = p | "R" >> beam.io.ReadFromJson("./sample_data/events.ndjson")
        keyed = rows | "K" >> beam.Map(lambda r: ("all", 1))
        n = keyed | "N" >> beam.combiners.Count.PerKey()
        n | "W" >> beam.io.WriteToText(OUT + "/jsoncount", num_shards=1, shard_name_template="")
    print("  json count:", open(OUT + "/jsoncount").read().strip())
except Exception as exc:
    print(f"  FAILED: {type(exc).__name__}: {str(exc)[:250]}")
