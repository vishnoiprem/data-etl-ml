"""Probe for notebook 03: sharded filenames, coders, avro/parquet sizing."""
import os
import shutil
import json
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam import coders
from apache_beam.coders import coders as coders_mod
import apache_beam.typehints as th

OPTS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
OUT = "/tmp/nbt3"
shutil.rmtree(OUT, ignore_errors=True)

print("=== 1. sharded filename ===")
with beam.Pipeline(options=OPTS) as p:
    (p | "C" >> beam.Create(["a", "b"])
       | "W" >> beam.io.WriteToText(OUT + "/sharded"))
print("sharded files:", sorted(os.listdir(OUT + "/sharded")))
print("coders.TupleCoder:", coders.TupleCoder)
import inspect as _i
from apache_beam.io.textio import WriteToText as _WTT
print("WriteToText sig:", _i.signature(_WTT.__init__))

print()
print("=== 2. coder registry for type hints ===")
for label, hint in [
    ("int", int),
    ("str", str),
    ("bytes", bytes),
    ("Dict[str, int]", th.Dict[str, int]),
    ("Tuple[int, str]", th.Tuple[int, str]),
    ("Tuple[int, str] coders", coders.TupleCoder),
]:
    from apache_beam.coders.typecoders import registry
    c = registry.get_coder(hint)
    print(f"  {label:28s} -> {type(c).__name__}")

print()
print("=== 3. element_type with/without hints ===")
with beam.Pipeline(options=OPTS) as p:
    bare = p | "C" >> beam.Create([("a", 1)])
    hinted = p | "C2" >> beam.Create([("a", 1)]) | "M" >> beam.Map(
        lambda kv: (kv[0], kv[1] + 1)
    ).with_output_types(th.Tuple[str, int])
    print("  bare  :", bare.element_type)
    print("  hinted:", hinted.element_type)

print()
print("=== 4. Avro write ===")
from apache_beam.io import avroio
SCHEMA = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}
with beam.Pipeline(options=OPTS) as p:
    rows = p | "C" >> beam.Create([{"order_id": "o1", "region": "EMEA", "amount": 10.5}])
    rows | "W" >> avroio.WriteToAvro(
        OUT + "/avro", schema=SCHEMA, num_shards=1, file_name_suffix=".avro"
    )
print("  avro files:", sorted(os.listdir(OUT + "/avro")))

print()
print("=== 5. Parquet write ===")
from apache_beam.io import parquetio
with beam.Pipeline(options=OPTS) as p:
    rows = p | "C" >> beam.Create([{"order_id": "o1", "region": "EMEA", "amount": 10.5}])
    rows | "W" >> parquetio.WriteToParquet(
        OUT + "/parquet", num_shards=1, file_name_suffix=".parquet"
    )
print("  parquet files:", sorted(os.listdir(OUT + "/parquet")))
