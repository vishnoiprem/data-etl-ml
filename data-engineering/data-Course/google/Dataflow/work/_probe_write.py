import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import sys
runner = sys.argv[1]
kind = sys.argv[2]

import apache_beam as beam
from apache_beam.pvalue import Row

def build(p):
    rows = (
        p
        | "C" >> beam.Create([Row(region="EMEA", n=1), Row(region="AMER", n=2)])
    )
    return rows

with beam.Pipeline(runner=runner) as p:
    rows = build(p)
    if kind == "csv":
        rows | "W" >> beam.io.WriteToCsv("./out/probe_csv")
    else:
        rows | "W" >> beam.io.WriteToJson("./out/probe_json")
print("OK")
