import apache_beam as beam
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

with beam.Pipeline() as p:
    rows = (
        p
        | "C" >> beam.Create([{"order_id": "o1", "region": "EMEA", "amount": 10.5}])
    )
    rows | "W" >> avroio.WriteToAvro("./out/probe_avro", schema=SCHEMA, num_shards=1, file_name_suffix=".avro")
print("OK")
