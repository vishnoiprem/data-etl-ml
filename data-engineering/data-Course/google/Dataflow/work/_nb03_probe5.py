import os
import shutil
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import avroio, parquetio
from apache_beam.typehints.schemas import schema_from_element_type

OPTS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
OUT = "/tmp/nbt3e"
shutil.rmtree(OUT, ignore_errors=True)

SCHEMA = {
    "type": "record", "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}

print("=== Avro write (with suffix) ===")
with beam.Pipeline(options=OPTS) as p:
    rows = p | "C" >> beam.Create([{"order_id": "o1", "region": "EMEA", "amount": 10.5}])
    rows | "W" >> avroio.WriteToAvro(OUT + "/avro", schema=SCHEMA, num_shards=1, file_name_suffix=".avro")
for root, dirs, files in os.walk(OUT):
    print("  ", root, files)

print()
print("=== Avro read back ===")
with beam.Pipeline(options=OPTS) as p:
    rows = p | "R" >> avroio.ReadFromAvro(OUT + "/avro*")
    print("  element_type:", rows.element_type)
    rows | "W" >> beam.io.WriteToText(OUT + "/avro_txt", num_shards=1, shard_name_template="")
print("  content:", open(OUT + "/avro_txt").read().strip())

print()
print("=== Parquet with explicit schema ===")
import apache_beam.typehints as th
PSCHEMA = th.Dict[str, th.Union[str, float]]
with beam.Pipeline(options=OPTS) as p:
    rows = (p | "C" >> beam.Create([{"order_id": "o1", "region": "EMEA", "amount": 10.5}])
              ).with_output_types(th.Dict[str, th.Union[str, float]])
    rows | "W" >> parquetio.WriteToParquet(OUT + "/pq", num_shards=1, file_name_suffix=".parquet")
for root, dirs, files in os.walk(OUT + "/pq"):
    print("  ", root, files)

print()
print("=== Parquet read back ===")
with beam.Pipeline(options=OPTS) as p:
    rows = p | "R" >> parquetio.ReadFromParquet(OUT + "/pq")
    print("  element_type:", rows.element_type)
    rows | "W" >> beam.io.WriteToText(OUT + "/pq_txt", num_shards=1, shard_name_template="")
print("  content:", open(OUT + "/pq_txt").read().strip())
