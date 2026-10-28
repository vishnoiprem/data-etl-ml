import os
import shutil
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

OPTS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
OUT = "/tmp/nbt3c"
shutil.rmtree(OUT, ignore_errors=True)

with beam.Pipeline(options=OPTS) as p:
    (p | "C" >> beam.Create(["a", "b"])
       | "W" >> beam.io.WriteToText(OUT + "/sharded"))

print("walk:")
for root, dirs, files in os.walk(OUT):
    print("  ", root, dirs, files)
print("listdir OUT:", os.listdir(OUT))
print("listdir OUT/sharded:", os.listdir(OUT + "/sharded"))
print()
print("WriteToText default shard template:")
import inspect
print(inspect.signature(beam.io.WriteToText.__init__))
