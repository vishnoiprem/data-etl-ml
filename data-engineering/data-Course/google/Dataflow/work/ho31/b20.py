# The pipeline declares three columns. The file has four.
rows = pipeline | "Read" >> beam.io.ReadFromCsv(
    "gs://bucket/orders_2026_01_15.csv",
    dtype={"order_id": str, "region": str, "amount": float},
)
