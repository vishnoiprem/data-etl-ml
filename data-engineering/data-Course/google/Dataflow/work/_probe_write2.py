import apache_beam as beam
from apache_beam.pvalue import Row
from apache_beam.options.pipeline_options import PipelineOptions
import sys

runner = sys.argv[1]
options = PipelineOptions(flags=[f"--runner={runner}"])

with beam.Pipeline(options=options) as p:
    rows = p | "C" >> beam.Create([Row(region="EMEA", n=1), Row(region="AMER", n=2)])
    rows | "W" >> beam.io.WriteToCsv("./out/probe_csv2")
print("OK")
