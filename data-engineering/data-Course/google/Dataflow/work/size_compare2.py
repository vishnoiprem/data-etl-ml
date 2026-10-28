import json, shutil
import apache_beam as beam
from apache_beam.io import parquetio
import pyarrow as pa

FIELDS = ["order_id","customer_id","order_ts","region","channel","currency","status","amount","product_id"]
SCHEMA = pa.schema([
    pa.field("order_id", pa.string()), pa.field("customer_id", pa.string()),
    pa.field("order_ts", pa.string()), pa.field("region", pa.string()),
    pa.field("channel", pa.string()), pa.field("currency", pa.string()),
    pa.field("status", pa.string()), pa.field("amount", pa.float64()),
    pa.field("product_id", pa.string()),
])
for d in ["out/fc2/csv","out/fc2/ndjson","out/fc2/pq_none","out/fc2/pq_snappy","out/fc2/pq_zstd"]:
    shutil.rmtree(d, ignore_errors=True)

with beam.Pipeline() as p:
    rows = (
        p | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "SkipHeader" >> beam.Filter(lambda l: not l.startswith("order_id"))
        | "Parse" >> beam.Map(lambda l: {**dict(zip(FIELDS, l.split(","))), "amount": float(l.split(",")[7])})
    )
    rows | "ToCsv" >> beam.Map(lambda d: ",".join(str(d[f]) for f in FIELDS)) | "WriteCsv" >> beam.io.WriteToText("out/fc2/csv", num_shards=1, shard_name_template="", header=",".join(FIELDS))
    rows | "ToJson" >> beam.Map(json.dumps) | "WriteJson" >> beam.io.WriteToText("out/fc2/ndjson", num_shards=1, shard_name_template="")
    rows | "WritePqNone" >> parquetio.WriteToParquet("out/fc2/pq_none", schema=SCHEMA, num_shards=1, codec="none", file_name_suffix=".parquet")
    rows | "WritePqSnappy" >> parquetio.WriteToParquet("out/fc2/pq_snappy", schema=SCHEMA, num_shards=1, codec="snappy", file_name_suffix=".parquet")
    rows | "WritePqZstd" >> parquetio.WriteToParquet("out/fc2/pq_zstd", schema=SCHEMA, num_shards=1, codec="zstd", file_name_suffix=".parquet")
print("DONE")
