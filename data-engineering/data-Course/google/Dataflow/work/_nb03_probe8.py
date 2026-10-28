import os
import shutil
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

OPTS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
OUT = "/tmp/nbt3h"
shutil.rmtree(OUT, ignore_errors=True)

for tmpl, label in [(None, "default"), ("", "empty"), ("-SSSS-of-SSSS", "dash")]:
    d = OUT + "/t" + str(label)
    with beam.Pipeline(options=OPTS) as p:
        (p | "C" >> beam.Create(["x"])
           | "W" >> beam.io.WriteToText(d, num_shards=1, shard_name_template=tmpl))
    for root, dirs, files in os.walk(d):
        print(f"  {label:8s}: {files}")
    if not os.path.exists(d):
        print(f"  {label:8s}: (dir does not exist)")

print()
print("=== WriteToText with trailing slash ===")
d = OUT + "/slash/"
with beam.Pipeline(options=OPTS) as p:
    (p | "C" >> beam.Create(["x"])
       | "W" >> beam.io.WriteToText(d, num_shards=1))
for root, dirs, files in os.walk(OUT + "/slash"):
    print(f"  {root} -> {files}")

print()
print("=== glob pattern on the output prefix ===")
print("  matches:", sorted(str(f) for f in __import__("pathlib").Path(OUT).glob("tdefault*")))
