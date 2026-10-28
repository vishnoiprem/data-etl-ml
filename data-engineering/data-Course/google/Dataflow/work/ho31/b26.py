import apache_beam as beam

with beam.Pipeline() as pipeline:
    (
        pipeline
        | "ReadParquet" >> beam.io.ReadFromParquet(
            "./out/hands_on/orders_parquet-00000-of-00001",
            as_rows=True,
        )
        | "Print" >> beam.Map(print)
    )
