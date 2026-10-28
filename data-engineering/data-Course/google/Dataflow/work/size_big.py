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
for d in ["out/big/csv","out/big/ndjson","out/big/pq","out/big/avro"]:
    shutil.rmtree(d, ignore_errors=True)
AVRO = {"type":"record","name":"Order","fields":[
    {"name":f,"type":"double" if f=="amount" else "string"} for f in FIELDS]}

with beam.Pipeline() as p:
    rows = (
        p | "Read" >> beam.io.ReadFromText("work/bigdata/orders.csv")
        | "SkipHeader" >> beam.Filter(lambda l: not l.startswith("order_id"))
        | "Parse" >> beam.Map(lambda l: {**dict(zip(FIELDS, l.split(","))), "amount": float(l.split(",")[7])})
    )
    rows | "ToCsv" >> beam.Map(lambda d: ",".join(str(d[f]) for f in FIELDS)) | "WriteCsv" >> beam.io.WriteToText("out/big/csv", num_shards=1, shard_name_template="", header=",".join(FIELDS))
    rows | "ToJson" >> beam.Map(json.dumps) | "WriteJson" >> beam.io.WriteToText("out/big/ndjson", num_shards=1, shard_name_template="")
    rows | "WritePq" >> parquetio.WriteToParquet("out/big/pq", schema=SCHEMA, num_shards=1, codec="snappy", file_name_suffix=".parquet")
    rows | "WriteAvro" >> beam.io.avroio.WriteToAvro("out/big/avro", schema=AVRO, num_shards=1, codec="deflate", file_name_suffix=".avro")
print("DONE")
