import apache_beam as beam


class ReturnsDict(beam.DoFn):
    def process(self, value):
        return {"k": value}


class YieldsDict(beam.DoFn):
    def process(self, value):
        yield {"k": value}


with beam.Pipeline() as p:
    source = p | "Create" >> beam.Create(["a", "b"])
    (
        source
        | "Yield" >> beam.ParDo(YieldsDict())
        | "Format" >> beam.Map(lambda d: f"k={d['k']}")
        | "Write" >> beam.io.WriteToText("./out/dict_yield", num_shards=1)
    )
