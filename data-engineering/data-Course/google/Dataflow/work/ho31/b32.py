import pyarrow as pa

ARROW_SCHEMA = pa.schema(
    [
        pa.field("order_id", pa.string()),
        pa.field("region", pa.string()),
        pa.field("amount", pa.float64()),
    ]
)
