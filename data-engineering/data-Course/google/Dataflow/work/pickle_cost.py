import apache_beam as beam
import apache_beam.typehints as th
from apache_beam.coders import coders
from apache_beam.coders.typecoders import registry

N = 100_000


def encode_all(elements, coder):
    return sum(len(coder.encode(e)) for e in elements)


hinted = [("o0001", "EMEA") for _ in range(N)]
unhinted = [{"order_id": "o0001", "region": "EMEA"} for _ in range(N)]

tuple_coder = registry.get_coder(th.Tuple[str, str])
dict_coder = registry.get_coder(dict)

tuple_bytes = encode_all(hinted, tuple_coder)
dict_bytes = encode_all(unhinted, dict_coder)

print(f"tuple elements: {N}")
print(f"  coder: {type(tuple_coder).__name__}")
print(f"  total bytes: {tuple_bytes:,}")
print(f"  bytes per element: {tuple_bytes / N:.2f}")

print(f"dict elements: {N}")
print(f"  coder: {type(dict_coder).__name__}")
print(f"  total bytes: {dict_bytes:,}")
print(f"  bytes per element: {dict_bytes / N:.2f}")

print(f"ratio (dict/tuple): {dict_bytes / tuple_bytes:.2f}x")
