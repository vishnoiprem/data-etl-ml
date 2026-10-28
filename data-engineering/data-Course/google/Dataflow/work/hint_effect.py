import sys
sys.path.insert(0, "project")
import apache_beam as beam
import apache_beam.typehints as th
from transforms import ParseOrderFn

with beam.Pipeline() as p:
    lines = p | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
    unannotated = lines | "ParseBare" >> beam.ParDo(ParseOrderFn())
    print("DoFn, no annotation ->", unannotated.element_type)
    annotated = lines | "ParseAnnotated" >> beam.ParDo(
        ParseOrderFn()
    ).with_output_types(th.Dict[str, th.Any])
    print("DoFn, annotated      ->", annotated.element_type)
