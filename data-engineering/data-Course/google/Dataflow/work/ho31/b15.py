from apache_beam.coders import typecoders

typecoders.registry.register_coder(Order, OrderCoder)
