import apache_beam as beam
from apache_beam.io import avroio
import apache_beam.typehints as th

with beam.Pipeline() as p:
    rows = p | "R" >> avroio.ReadFromAvro("./out/probe_avro*")
    print("element_type:", rows.element_type)
    rows | "W" >> beam.io.WriteToText("./out/probe_avro_read", num_shards=1, shard_name_template="")
