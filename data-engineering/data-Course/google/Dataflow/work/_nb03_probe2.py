import os
import shutil
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

OPTS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
OUT = "/tmp/nbt3b"
shutil.rmtree(OUT, ignore_errors=True)

with beam.Pipeline(options=OPTS) as p:
    (p | "C" >> beam.Create(["a", "b"])
       | "W" >> beam.io.WriteToText(OUT + "/sharded"))

print("exists:", os.path.exists(OUT))
for root, dirs, files in os.walk(OUT):
    print(root, dirs, files)
