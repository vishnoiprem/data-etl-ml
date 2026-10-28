"""Write the same orders as CSV, NDJSON and Parquet, then compare sizes."""
import json, shutil
import apache_beam as beam
from apache_beam.io import parquetio
import pyarrow as pa

FIELDS = ["order_id","customer_id","order_ts","region","channel","currency","status","amount","product_id"]
SCHEMA = pa.schema([
    pa.field("order_id", pa.string()),
    pa.field("customer_id", pa.string()),
    pa.field("order_ts", pa.string()),
    pa.field("region", pa.string()),
    pa.field("channel", pa.string()),
    pa.field("currency", pa.string()),
    pa.field("status", pa.string()),
    pa.field("amount", pa.float64()),
    pa.field("product_id", pa.string()),
])

for d in ["out/format_cmp/csv", "out/format_cmp/ndjson", "out/format_cmp/parquet"]:
    shutil.rmtree(d, ignore_errors=True)

def to_csv(d):
    return ",".join(str(d[f]) for f in FIELDS)

def to_ndjson(d):
    return json.dumps(d)

with beam.Pipeline() as p:
    rows = (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "SkipHeader" >> beam.Filter(lambda l: not l.startswith("order_id"))
        | "Parse" >> beam.Map(lambda l: {**dict(zip(FIELDS, l.split(","))), "amount": float(l.split(",")[7])})
    )
    rows | "ToCsv" >> beam.Map(to_csv) | "WriteCsv" >> beam.io.WriteToText("out/format_cmp/csv", num_shards=1, shard_name_template="", header=",".join(FIELDS))
    rows | "ToJson" >> beam.Map(to_ndjson) | "WriteJson" >> beam.io.WriteToText("out/format_cmp/ndjson", num_shards=1, shard_name_template="")
    rows | "WriteParquet" >> parquetio.WriteToParquet("out/format_cmp/parquet", schema=SCHEMA, num_shards=1, file_name_suffix=".parquet")
print("DONE")
