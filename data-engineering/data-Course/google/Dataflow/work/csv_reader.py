"""Read the orders CSV with the pandas-backed ReadFromCsv."""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(flags=["--runner=BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    rows = p | "ReadCsv" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
    print("element_type:", rows.element_type)
