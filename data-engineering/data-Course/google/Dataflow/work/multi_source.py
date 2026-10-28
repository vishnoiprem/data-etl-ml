import apache_beam as beam
import apache_beam.typehints as th

INPUTS = {"csv": "./sample_data/orders.csv", "ndjson": "./sample_data/orders.ndjson"}


def build(pipeline):
    tagged_branches = []
    for source_name, path in INPUTS.items():
        branch = (
            pipeline
            | f"Read{source_name.title()}" >> beam.io.ReadFromText(path)
            | f"Tag{source_name.title()}" >> beam.Map(
                lambda line, name=source_name: (name, line)
            ).with_output_types(th.Tuple[str, str])
        )
        tagged_branches.append(branch)
    return tagged_branches | "Flatten" >> beam.Flatten()


with beam.Pipeline() as p:
    merged = build(p)
    counts = (
        merged
        | "CountBySource" >> beam.combiners.Count.PerKey()
        | "FormatCounts" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        | "WriteCounts" >> beam.io.WriteToText(
            "./out/source_counts", num_shards=1, shard_name_template=""
        )
    )
