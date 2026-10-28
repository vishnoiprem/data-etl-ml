import apache_beam as beam
from apache_beam.io import parquetio, avroio
import pyarrow as pa

SCHEMA = pa.schema([pa.field("order_id", pa.string()), pa.field("region", pa.string()), pa.field("amount", pa.float64())])
AVRO = {"type":"record","name":"Order","fields":[
    {"name":"order_id","type":"string"},{"name":"region","type":"string"},{"name":"amount","type":"double"}]}

def try_pq(codec):
    try:
        with beam.Pipeline() as p:
            rows = p | "C" >> beam.Create([{"order_id":"o1","region":"EMEA","amount":10.5}])
            rows | "W" >> parquetio.WriteToParquet(f"./out/c2_pq_{codec}", schema=SCHEMA, num_shards=1, codec=codec, file_name_suffix=".parquet")
        return "OK"
    except Exception as e:
        return f"FAIL {type(e).__name__}: {str(e)[:80]}"

def try_avro(codec):
    try:
        with beam.Pipeline() as p:
            rows = p | "C" >> beam.Create([{"order_id":"o1","region":"EMEA","amount":10.5}])
            rows | "W" >> avroio.WriteToAvro(f"./out/c2_avro_{codec}", schema=AVRO, num_shards=1, codec=codec, file_name_suffix=".avro")
        return "OK"
    except Exception as e:
        return f"FAIL {type(e).__name__}: {str(e)[:80]}"

for c in ["none","snappy","gzip","brotli","zstd","lz4"]:
    print("parquet", c, try_pq(c))
for c in ["null","deflate","snappy","bzip2","zstandard","xz"]:
    print("avro   ", c, try_avro(c))
