import os
import shutil
import collections
import typing
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import parquetio
from apache_beam.typehints.schemas import schema_from_element_type

import sys
OPTS = PipelineOptions(["--runner", sys.argv[1] if len(sys.argv)>1 else "BundleBasedDirectRunner"])
OUT = "/tmp/nbt3g"
shutil.rmtree(OUT, ignore_errors=True)

Order = typing.NamedTuple("Order", [("order_id", str), ("region", str), ("amount", float)])
print("schema from namedtuple:", schema_from_element_type(Order))

print()
print("=== Parquet with namedtuple rows ===")
with beam.Pipeline(options=OPTS) as p:
    rows = p | "C" >> beam.Create([Order("o1", "EMEA", 10.5), Order("o2", "AMER", 3.25)])
    rows | "W" >> parquetio.WriteToParquet(
        OUT + "/pq", num_shards=1, file_name_suffix=".parquet"
    )
for root, dirs, files in os.walk(OUT):
    print("  ", root, files)

print()
print("=== Parquet read back ===")
with beam.Pipeline(options=OPTS) as p:
    rows = p | "R" >> parquetio.ReadFromParquet(OUT + "/pq*")
    print("  element_type:", rows.element_type)
    rows | "W" >> beam.io.WriteToText(OUT + "/pq_txt", num_shards=1, shard_name_template="")
print("  content:", open(OUT + "/pq_txt").read().strip())

print()
print("=== WriteToText shard template variants ===")
for tmpl, label in [(None, "default"), ("", "empty"), ("-SSSS-of-SSSS", "dash")]:
    d = OUT + "/t" + str(label)
    with beam.Pipeline(options=OPTS) as p:
        (p | "C" >> beam.Create(["x"])
           | "W" >> beam.io.WriteToText(d, num_shards=1, shard_name_template=tmpl))
    for root, dirs, files in os.walk(d):
        print(f"  {label:8s}: {files}")
