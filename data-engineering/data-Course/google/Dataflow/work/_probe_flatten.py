import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

OPTS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=OPTS) as p:
    src = p | "C" >> beam.Create([("csv", "EMEA"), ("csv", "AMER"), ("json", "EMEA")])
    print("source element_type:", src.element_type)
    counted = src | "Cnt" >> beam.combiners.Count.PerKey()
    print("counted element_type:", counted.element_type)
    counted | "W" >> beam.io.WriteToText("/tmp/flat_probe", num_shards=1, shard_name_template="")

print(open("/tmp/flat_probe").read())
