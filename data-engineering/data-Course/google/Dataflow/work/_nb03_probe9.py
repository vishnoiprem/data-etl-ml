import os
import shutil
import pathlib
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

OPTS = PipelineOptions(["--runner", "BundleBasedDirectRunner"])
OUT = "/tmp/nbt3i"
shutil.rmtree(OUT, ignore_errors=True)

for tmpl, label in [(None, "default"), ("", "empty"), ("-SSSS-of-SSSS", "dash")]:
    d = OUT + "/t" + str(label)
    with beam.Pipeline(options=OPTS) as p:
        (p | "C" >> beam.Create(["x"])
           | "W" >> beam.io.WriteToText(d, num_shards=1, shard_name_template=tmpl))
    files = [f.name for f in pathlib.Path(d).glob("*")] if os.path.isdir(d) else ["<no dir>"]
    print(f"  {label:8s}: {files}")

print()
print("  glob tdefault*:", sorted(f.name for f in pathlib.Path(OUT).glob("tdefault*")))
print("  glob t*  :", sorted(f.name for f in pathlib.Path(OUT).glob("t*")))
