AVRO_SCHEMA = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "region", "type": "string"},
        {"name": "amount", "type": "double"},
    ],
}

rows | "WriteAvro" >> beam.io.WriteToAvro(
    "gs://bucket/orders", schema=AVRO_SCHEMA, num_shards=1
)
