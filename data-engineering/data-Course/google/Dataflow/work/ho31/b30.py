from apache_beam.coders import coders

coders.registry.register_coder(Order, OrderCoder)
orders | "Parse" >> beam.ParDo(ParseOrderFn()).with_output_types(Order)
