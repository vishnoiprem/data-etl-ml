from apache_beam.coders import registry

print(registry.get_coder(int))    # VarIntCoder
print(registry.get_coder(str))    # StrUtf8Coder
print(registry.get_coder(dict))   # FastPrimitivesCoder
