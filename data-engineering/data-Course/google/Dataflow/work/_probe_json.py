import apache_beam as beam
import sys
runner = sys.argv[1]
with beam.Pipeline(runner=runner) as p:
    rows = p | "R" >> beam.io.ReadFromJson("./sample_data/orders.ndjson")
    print("JSON element_type:", rows.element_type)
