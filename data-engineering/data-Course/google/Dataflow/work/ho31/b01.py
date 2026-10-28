from transforms import ParseOrderFn

with beam.Pipeline() as pipeline:
    orders = (
        pipeline
        | "Create" >> beam.Create([VALID_LINE])
        | "Parse" >> beam.ParDo(ParseOrderFn())
    )
    print(orders.element_type)   # Any
