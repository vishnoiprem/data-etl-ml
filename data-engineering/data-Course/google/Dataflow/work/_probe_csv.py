import apache_beam as beam
import sys
runner = sys.argv[1]
with beam.Pipeline(runner=runner) as p:
    rows = p | "R" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
    print("CSV element_type:", rows.element_type)
