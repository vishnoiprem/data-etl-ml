import apache_beam as beam
from apache_beam.coders import coders
import apache_beam.typehints as th

with beam.Pipeline() as p:
    raw = p | "ReadBytes" >> beam.io.ReadFromText(
        "./sample_data/orders.csv",
        coder=coders.BytesCoder(),
    )
    print("ReadFromText ->", raw.element_type)

with beam.Pipeline() as p:
    (p | "Create" >> beam.Create(["1", "2"]) | "Parse" >> beam.Map(int, coder=coders.VarIntCoder()))

with beam.Pipeline() as p:
    (p | "Create" >> beam.Create([1, 2, 3]) | "Square" >> beam.Map(lambda x: x * x).with_output_types(int))

class ParseAmount(beam.DoFn):
    @beam.typehints.with_output_types(th.Optional[float])
    def process(self, line: str):
        try:
            return float(line.strip())
        except ValueError:
            return None

print("all ok")
