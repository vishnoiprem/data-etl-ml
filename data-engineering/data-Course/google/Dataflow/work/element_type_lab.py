import apache_beam as beam
from apache_beam.coders import coders
import apache_beam.typehints as th

with beam.Pipeline() as p:
    text = p | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
    print("ReadFromText   ->", text.element_type)

    tagged = (
        p
        | "Create" >> beam.Create(["EMEA", "AMER"])
        | "Tag" >> beam.Map(lambda r: ("orders", r)).with_output_types(
            th.Tuple[str, str]
        )
    )
    print("Tagged tuple   ->", tagged.element_type)

    optional = (
        p
        | "Create2" >> beam.Create(["1.5"])
        | "ToFloat" >> beam.Map(float).with_output_types(th.Optional[float])
    )
    print("Optional float ->", optional.element_type)

    as_bytes = p | "ReadBytes" >> beam.io.ReadFromText(
        "./sample_data/orders.csv",
        coder=coders.BytesCoder(),
    )
    print("Read as bytes  ->", as_bytes.element_type)
