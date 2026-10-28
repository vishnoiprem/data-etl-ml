import shutil, sys
from pathlib import Path
import apache_beam as beam
sys.path.insert(0, str(Path(__file__).resolve().parent))
from transforms import ParseOrderFn, RevenueByRegionFn, format_summary_csv

INPUT = "./sample_data/orders.csv"
OUT_FILTER_FIRST = "./out/hands_on/summary_filter_first"
OUT_FILTER_LAST = "./out/hands_on/summary_filter_last"


def build(pipeline, output_path, *, filter_before_keying):
    lines = pipeline | "ReadOrders" >> beam.io.ReadFromText(INPUT)
    orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())

    if filter_before_keying:
        kept = orders | "KeepComplete" >> beam.Filter(
            lambda order: order["status"] == "complete"
        )
        keyed = kept | "KeyByRegion" >> beam.Map(
            lambda order: (order["region"], order)
        )
    else:
        keyed = orders | "KeyByRegion" >> beam.Map(
            lambda order: (order["region"], order)
        )
        kept = keyed | "KeepComplete" >> beam.Filter(
            lambda pair: pair[1]["status"] == "complete"
        )

    summary = kept | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())

    (
        summary
        | "FormatCsv" >> beam.Map(format_summary_csv)
        | "WriteSummary" >> beam.io.WriteToText(
            output_path,
            header="region,order_count,revenue_eur",
            num_shards=1,
            shard_name_template="",
        )
    )


def main():
    for name, output, before in (
        ("filter_first", OUT_FILTER_FIRST, True),
        ("filter_last", OUT_FILTER_LAST, False),
    ):
        shutil.rmtree(output, ignore_errors=True)
        with beam.Pipeline() as pipeline:
            build(pipeline, output, filter_before_keying=before)

    first = open(OUT_FILTER_FIRST, encoding="utf-8").read()
    last = open(OUT_FILTER_LAST, encoding="utf-8").read()
    print("filter-first output:")
    print(first)
    print("filter-last output:")
    print(last)
    print("IDENTICAL" if first == last else "DIFFERENT")


if __name__ == "__main__":
    main()
