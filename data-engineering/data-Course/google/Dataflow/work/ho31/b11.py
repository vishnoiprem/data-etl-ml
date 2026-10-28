from apache_beam.coders import RowCoder

coder = RowCoder(schema, force_deterministic=True)
