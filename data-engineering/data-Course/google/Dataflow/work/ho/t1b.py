import shutil
import apache_beam as beam

INPUT = "./sample_data/orders.csv"
OUT_FILTER_FIRST = "./out/hands_on/shuffle_filter_first"
OUT_FILTER_LAST = "./out/hands_on/shuffle_filter_last"


def count_elements(pipeline, *, filter_before_keying):
    """Count the elements that enter the keyed stage."""
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
        keyed | "CountElements" >> beam.combiners.Count.Globally()
        kept = keyed | "KeepComplete" >> beam.Filter(
            lambda pair: ",complete," in pair[1]
        )
    total = kept | "CountElements" >> beam.combiners.Count.Globally()
    return total
