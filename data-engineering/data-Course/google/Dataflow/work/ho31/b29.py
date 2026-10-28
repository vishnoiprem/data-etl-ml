# WRONG — does not exist
from apache_beam.rows import Row

# RIGHT — dynamic row
from apache_beam.pvalue import Row

# RIGHT — schema'd row
from apache_beam.coders import typecoders

typecoders.registry.register_row(Order)
