from apache_beam.coders import NullableCoder, FloatCoder

coder = NullableCoder(FloatCoder())
print(coder.encode(None))    # b'\x00'
print(coder.encode(1.5))     # b'\x01?\xf8\x00\x00\x00\x00\x00\x00'
print(coder.decode(b'\x00')) # None
