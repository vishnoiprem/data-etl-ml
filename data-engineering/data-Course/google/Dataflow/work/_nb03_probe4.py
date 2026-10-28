import os
import shutil
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam import coders
from apache_beam.coders.typecoders import registry
import apache_beam.typehints as th
import inspect

OPTS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
OUT = "/tmp/nbt3d"
shutil.rmtree(OUT, ignore_errors=True)

print("=== WriteToText signature ===")
print(inspect.signature(beam.io.WriteToText.__init__))

print()
print("=== coder registry ===")
for label, hint in [
    ("int", int), ("str", str), ("bytes", bytes), ("float", float),
    ("Dict[str, int]", th.Dict[str, int]),
    ("Tuple[int, str]", th.Tuple[int, str]),
    ("Tuple[int, str] via coders", coders.TupleCoder),
]:
    c = registry.get_coder(hint)
    print(f"  {label:28s} -> {type(c).__name__}")

print()
print("=== element_type with/without hints ===")
with beam.Pipeline(options=OPTS) as p:
    bare = p | "C" >> beam.Create([("a", 1)])
    hinted = p | "C2" >> beam.Create([("a", 1)]) | "M" >> beam.Map(
        lambda kv: (kv[0], kv[1] + 1)).with_output_types(th.Tuple[str, int])
    print("  bare  :", bare.element_type)
    print("  hinted:", hinted.element_type)

print()
print("=== Avro write ===")
from apache_beam.io import avroio
SCHEMA = {
    "type": "record", "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}
with beam.Pipeline(options=OPTS) as p:
    rows = p | "C" >> beam.Create([{"order_id": "o1", "region": "EMEA", "amount": 10.5}])
    rows | "W" >> avroio.WriteToAvro(OUT + "/avro", schema=SCHEMA, num_shards=1, file_name_suffix=".avro")
for root, dirs, files in os.walk(OUT + "/avro"):
    print("  ", root, files)

print()
print("=== Parquet write ===")
from apache_beam.io import parquetio
with beam.Pipeline(options=OPTS) as p:
    rows = p | "C" >> beam.Create([{"order_id": "o1", "region": "EMEA", "amount": 10.5}])
    rows | "W" >> parquetio.WriteToParquet(OUT + "/parquet", num_shards=1, file_name_suffix=".parquet")
for root, dirs, files in os.walk(OUT + "/parquet"):
    print("  ", root, files)

print()
print("=== Avro read back ===")
with beam.Pipeline(options=OPTS) as p:
    rows = p | "R" >> avroio.ReadFromAvro(OUT + "/avro")
    print("  avro element_type:", rows.element_type)
    n = rows | "N" >> beam.combiners.Count()
    n | "W" >> beam.io.WriteToText(OUT + "/avro_count", num_shards=1, shard_name_template="")
print("  avro_count:", open(OUT + "/avro_count").read().strip())

print()
print("=== Parquet read back ===")
with beam.Pipeline(options=OPTS) as p:
    rows = p | "R" >> parquetio.ReadFromParquet(OUT + "/parquet")
    print("  parquet element_type:", rows.element_type)
    n = rows | "N" >> beam.combiners.Count()
    n | "W" >> beam.io.WriteToText(OUT + "/pq_count", num_shards=1, shard_name_template="")
print("  pq_count:", open(OUT + "/pq_count").read().strip())
