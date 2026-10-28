"""Print the pipeline graph so you can see the fork."""

import apache_beam as beam

INPUT = "./sample_data/orders.csv"


def show_graph(pipeline):
    """Print each step of the pipeline graph."""
    for applied in pipeline.transforms_stack:
        for part in applied.parts:
            print(f"  {part.full_label} | {type(part.transform).__name__}")


with beam.Pipeline() as p:
    summary = (
        p
        | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        | "KeyByRegion" >> beam.Map(lambda line: (line.split(",")[3], 1))
        | "CountByRegion" >> beam.combiners.Count.PerKey()
    )

    summary | "WriteA" >> beam.io.WriteToText("./out/graph_a", num_shards=1)
    summary | "WriteB" >> beam.io.WriteToText("./out/graph_b", num_shards=1)
    summary | "WriteC" >> beam.io.WriteToText("./out/graph_c", num_shards=1)

    print("--- pipeline graph ---")
    show_graph(p)
