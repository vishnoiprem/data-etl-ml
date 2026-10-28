"""Fix the DLQ reconciliation cell: use regex, avoid literal-tab matching."""

import re
from pathlib import Path

GEN = Path(__file__).resolve().parent / "gen_nb_09.py"
src = GEN.read_text()

pattern = re.compile(
    r'    ok = classified\[None\]\n'
    r'    not_ok = classified\["dlq"\]\n'
    r'    _ = ok \| "Format" >> beam\.Map\(\n'
    r'        lambda record: f"\{record\.get\(\'order_id\', \'\?\'\)\}"\)\n'
    r'    _ = ok \| "Write" >> beam\.io\.WriteToText\(str\(DLQ_RECON_DIR / "ok"\)\)\n'
    r'    _ = \(not_ok\n'
    r'         \| "Format" >> beam\.Map\(lambda item: f"\{item\[0\]\}.*?\{item\[1\]\}"\)\n'
    r'         \| "Write" >> beam\.io\.WriteToText\(str\(DLQ_RECON_DIR / "dlq"\)\)\)',
    re.DOTALL,
)

replacement = (
    '    ok = classified[None]\n'
    '    not_ok = classified["dlq"]\n'
    '    _ = (ok\n'
    '         | "Format" >> beam.Map(\n'
    '             lambda record: "{0}".format(record.get("order_id", "?")))\n'
    '         | "Write" >> beam.io.WriteToText(str(DLQ_RECON_DIR / "ok")))\n'
    '    _ = (not_ok\n'
    '         | "FormatDlq" >> beam.Map(\n'
    '             lambda item: "{0}|{1}".format(item[0], item[1]))\n'
    '         | "Write" >> beam.io.WriteToText(str(DLQ_RECON_DIR / "dlq")))'
)

new_src, count = pattern.subn(replacement, src)
print(f"replacements: {count}")
if count:
    GEN.write_text(new_src)
