from apache_beam.coders import coders
from apache_beam.coders.typecoders import registry
import apache_beam.typehints as th

HINTS = [
    ("int", int), ("float", float), ("str", str), ("bytes", bytes),
    ("bool", bool), ("bare dict", dict),
    ("Dict[str, int]", th.Dict[str, int]),
    ("Tuple[int, str]", th.Tuple[int, str]),
    ("Optional[str]", th.Optional[str]),
    ("List[int]", th.List[int]),
]
for label, hint in HINTS:
    coder = registry.get_coder(hint)
    print(f"{label:20s} -> {type(coder).__name__:32s} deterministic={coder.is_deterministic()}")
