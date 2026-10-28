from apache_beam.coders import (
    BooleanCoder,
    BytesCoder,
    FastPrimitivesCoder,
    FloatCoder,
    PickleCoder,
    StrUtf8Coder,
    VarIntCoder,
)

for coder in (
    StrUtf8Coder(),
    VarIntCoder(),
    FloatCoder(),
    BytesCoder(),
    BooleanCoder(),
    FastPrimitivesCoder(),
    PickleCoder(),
):
    print(f"{type(coder).__name__:<22} deterministic={coder.is_deterministic()}")
