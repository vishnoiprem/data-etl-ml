"""Probe the interactive runner's real behaviour, under IPython."""

import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "_probe_interactive.txt"

SCRIPT = r'''
from IPython.core.interactiveshell import InteractiveShell

# Stand up a real IPython shell, which is what the interactive runner needs.
shell = InteractiveShell.instance()

import apache_beam as beam
import apache_beam.runners.interactive.interactive_beam as ib
import pkgutil
import apache_beam.runners as runners

names = sorted(
    m.name for m in pkgutil.iter_modules(runners.__path__)
    if not m.name.startswith("_")
)
print("ALL RUNNER MODULES:", ", ".join(names))

with beam.Pipeline() as p:
    source = p | "Create" >> beam.Create([1, 2, 3, 4, 5])
    doubled = source | "Double" >> beam.Map(lambda x: x * 2)
    big = doubled | "Keep big" >> beam.Filter(lambda x: x > 4)

print("COLLECT:", ib.collect(big))
print("COLLECT SOURCE:", ib.collect(source))

try:
    v = p.visualize()
    print("VISUALIZE TYPE:", type(v).__name__)
    print("VISUALIZE HEAD:", str(v)[:120])
except Exception as e:
    print("VISUALIZE FAILED:", type(e).__name__, e)

for name in ("collect", "show", "visualize", "display"):
    print(f"HAS {name}:", hasattr(ib, name))
'''

result = subprocess.run(
    [sys.executable, "-c", SCRIPT], capture_output=True, text=True
)
OUT.write_text(
    f"=== exit {result.returncode} ===\n=== STDOUT ===\n{result.stdout}\n"
    f"=== STDERR ===\n{result.stderr[-2500:]}\n"
)
print(OUT)
