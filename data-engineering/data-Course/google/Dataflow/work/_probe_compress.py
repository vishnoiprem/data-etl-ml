import apache_beam as beam
from apache_beam.io import parquetio, avroio
import pyarrow as pa

SCHEMA = pa.schema([
    pa.field("order_id", pa.string()),
    pa.field("region", pa.string()),
    pa.field("amount", pa.float64()),
])
AVRO = {"type":"record","name":"Order","fields":[
    {"name":"order_id","type":"string"},
    {"name":"region","type":"string"},
    {"name":"amount","type":"double"}]}

for codec in ["none", "snappy", "gzip", "zstd"]:
    with beam.Pipeline() as p:
        rows = p | "C" >> beam.Create([{"order_id": "o1", "region": "EMEA", "amount": 10.5}])
        rows | "W" >> parquetio.WriteToParquet(f"./out/codec_pq_{codec}", schema=SCHEMA, num_shards=1, codec=codec, file_name_suffix=".parquet")

for codec in ["deflate", "snappy", "bzip2", "zstandard"]:
    try:
        with beam.Pipeline() as p:
            rows = p | "C" >> beam.Create([{"order_id": "o1", "region": "EMEA", "amount": 10.5}])
            rows | "W" >> avroio.WriteToAvro(f"./out/codec_avro_{codec}", schema=AVRO, num_shards=1, codec=codec, file_name_suffix=".avro")
        print("avro codec OK:", codec)
    except Exception as e:
        print("avro codec FAIL:", codec, type(e).__name__, str(e)[:120])
