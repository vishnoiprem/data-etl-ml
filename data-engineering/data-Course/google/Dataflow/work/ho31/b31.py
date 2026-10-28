# WRONG
from apache_beam.coders import coders
coders.registry.register_coder(Order, OrderCoder)

# RIGHT
from apache_beam.coders import typecoders
typecoders.registry.register_coder(Order, OrderCoder)
