import os
import shutil

import apache_beam as beam
from apache_beam.io.filesystems import FileSystems
from apache_beam.io.textio import WriteToText

shutil.rmtree("./out/gcs_demo", ignore_errors=True)
os.makedirs("./out/gcs_demo", exist_ok=True)

# Part 2 - filesystem registry
print("gs://bucket/path ->", FileSystems.get_scheme("gs://bucket/path"))
print("./local/path    ->", FileSystems.get_scheme("./local/path"))
print("exists ./sample_data/orders.csv:", FileSystems.exists("./sample_data/orders.csv"))
print("exists ./nope.csv:", FileSystems.exists("./nope.csv"))

# Part 3 - shard naming
with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(["a", "b"])
        | "WriteOneShard" >> WriteToText(
            "./out/gcs_demo/shard_demo",
            num_shards=1,
            shard_name_template="",
        )
    )

print("shard_demo files:", sorted(os.listdir("./out/gcs_demo")))

# Part 4 - shard explosion
with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([f"key-{i:04d}" for i in range(500)])
        | "Explode" >> beam.FlatMap(
            lambda key: [f"{key}-part-{j}" for j in range(4)]
        )
        | "WriteMany" >> WriteToText(
            "./out/gcs_demo/many",
            shard_name_template="",
        )
    )

with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create([f"key-{i:04d}" for i in range(500)])
        | "Explode" >> beam.FlatMap(
            lambda key: [f"{key}-part-{j}" for j in range(4)]
        )
        | "WriteFew" >> WriteToText(
            "./out/gcs_demo/few",
            num_shards=8,
        )
    )

print("many files:", len([f for f in os.listdir("./out/gcs_demo") if f.startswith("many")]))
print("few files :", len([f for f in os.listdir("./out/gcs_demo") if f.startswith("few")]))

# Part 2 - match
for result in FileSystems.match(["./out/gcs_demo/*"]):
    for metadata in result.metadata_list:
        print("  ", metadata.path, metadata.size_in_bytes, "bytes")

# Part 5 - read back
with beam.Pipeline() as p:
    (
        p
        | "ReadBack" >> beam.io.ReadFromText("./out/gcs_demo/few*")
        | "CountLines" >> beam.Map(lambda line: len(line))
        | "PrintLines" >> beam.Map(print)
    )
