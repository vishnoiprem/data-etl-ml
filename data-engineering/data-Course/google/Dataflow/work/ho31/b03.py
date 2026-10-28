from apache_beam.coders import StrUtf8Coder

lines = pipeline | "Read" >> beam.io.ReadFromText(path, coder=StrUtf8Coder())
