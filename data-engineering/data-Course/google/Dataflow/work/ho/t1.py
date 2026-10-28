import shutil
import apache_beam as beam

INPUT = "./sample_data/orders.csv"
OUT_FILTER_FIRST = "./out/hands_on/shuffle_filter_first"
OUT_FILTER_LAST = "./out/hands_on/shuffle_filter_last"


def count_elements(pipeline, *, filter_before_keying):
    lines = pipeline | "ReadOrders" >> beam.io.ReadFromText(INPUT)
    if filter_before_keying:
        kept = lines | "KeepComplete" >> beam.Filter(
            lambda line: ",complete," in line
        )
        keyed = kept | "KeyByRegion" >> beam.Map(
            lambda line: (line.split(",")[3], line)
        )
    else:
        keyed = lines | "KeyByRegion" >> beam.Map(
            lambda line: (line.split(",")[3], line)
        )
        kept = keyed | "KeepComplete" >> beam.Filter(
            lambda pair: ",complete," in pair[1]
        )
    total = kept | "CountElements" >> beam.combiners.Count.Globally()
    return total


def main():
    for name, output, before in (
        ("filter-first", OUT_FILTER_FIRST, True),
        ("filter-last", OUT_FILTER_LAST, False),
    ):
        shutil.rmtree(output, ignore_errors=True)
        with beam.Pipeline() as pipeline:
            counted = count_elements(pipeline, filter_before_keying=before)
            (
                counted
                | f"Write{name}" >> beam.io.WriteToText(
                    output, num_shards=1, shard_name_template=""
                )
            )
        with open(output, encoding="utf-8") as handle:
            print(f"{name}: {handle.read().strip()} elements enter the shuffle")


if __name__ == "__main__":
    main()
