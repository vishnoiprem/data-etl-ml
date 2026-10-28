from apache_beam.coders import FastPrimitivesCoder

print(FastPrimitivesCoder().is_deterministic())
# False
