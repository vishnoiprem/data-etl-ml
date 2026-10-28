import apache_beam as beam
import sys
which = sys.argv[1]
RUNNERS = {
    "class": beam.runners.direct.direct_runner.BundleBasedDirectRunner,
    "string": "BundleBasedDirectRunner",
    "prism": "PrismRunner",
}
with beam.Pipeline(runner=RUNNERS[which]) as p:
    rows = p | "R" >> beam.io.ReadFromCsv("./sample_data/orders.csv")
    print("element_type:", rows.element_type)
