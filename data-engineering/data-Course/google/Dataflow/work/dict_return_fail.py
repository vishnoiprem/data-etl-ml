import apache_beam as beam

class ReturnsDict(beam.DoFn):
    def process(self, value):
        return {"k": value}

with beam.Pipeline() as p:
    source = p | "Create" >> beam.Create(["a", "b"])
    (
        source
        | "Ret" >> beam.ParDo(ReturnsDict())
        | "Write" >> beam.io.WriteToText("./out/dict_ret", num_shards=1)
    )
