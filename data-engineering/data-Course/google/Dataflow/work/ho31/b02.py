from apache_beam.coders import FastPrimitivesCoder

coder = FastPrimitivesCoder()
coder.encode("hello")        # a compact varint-tagged encoding
coder.encode({"a": 1})       # also native
coder.encode(SomeClass())    # falls back to pickle
