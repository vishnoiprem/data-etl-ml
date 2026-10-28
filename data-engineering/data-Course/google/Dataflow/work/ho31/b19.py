from apache_beam.io.avroio import avro_schema_to_beam_schema

beam_schema = avro_schema_to_beam_schema(avro_schema)
