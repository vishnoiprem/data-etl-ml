import os
import shutil
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import parquetio
import apache_beam.typehints as th

OPTS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
OUT = "/tmp/nbt3f"
shutil.rmtree(OUT, ignore_errors=True)

print("=== Parquet: hint on the transform ===")
with beam.Pipeline(options=OPTS) as p:
    rows = p | "C" >> beam.Create([{"order_id": "o1", "region": "EMEA", "amount": 10.5}])
    rows | "W" >> parquetio.WriteToParquet(
        OUT + "/pq", num_shards=1, file_name_suffix=".parquet"
    ).with_output_types(th.Dict[str, th.Union[str, float]])
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
print("=== Parquet via schema_from_element_type on a namedtuple ===")
from apache_beam.typehints.schemas import schema_from_element_type
import collections
Order = collections.namedtuple("Order", ["order_id", "region", "amount"])
print("  schema:", schema_from_element_type(Order))
