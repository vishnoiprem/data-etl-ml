"""Check every "Expected output" block in the modules against a real execution.

Each `💻 Runs locally` code block in the seven modules is paired with a verbatim
`Expected output:` block.  Those blocks were pasted from real runs; this script is
what keeps them honest.

Run from `practice/`:  python3 _verify_modules.py
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent

BLOCK = re.compile(
    r"```python\n(.*?)```\n\nExpected output:\n\n```text\n(.*?)```",
    re.S,
)


def main() -> int:
    mismatches = 0
    checked = 0

    for path in sorted(HERE.glob("0*.md")):
        for match in BLOCK.finditer(path.read_text(encoding="utf-8")):
            code, expected = match.group(1), match.group(2)
            checked += 1

            with tempfile.NamedTemporaryFile(
                "w", suffix=".py", delete=False, dir=HERE
            ) as handle:
                handle.write(code)
                script = handle.name

            try:
                result = subprocess.run(
                    [sys.executable, script],
                    capture_output=True,
                    text=True,
                    cwd=HERE,
                )
            finally:
                os.unlink(script)

            actual = result.stdout.rstrip("\n")
            if actual != expected.rstrip("\n"):
                mismatches += 1
                print(f"MISMATCH {path.name}")
                print("--- expected ---")
                print(expected.rstrip("\n"))
                print("--- actual ---")
                print(actual)
                if result.stderr:
                    print("--- stderr ---")
                    print(result.stderr.rstrip("\n"))

    print(f"\nblocks checked: {checked}   mismatches: {mismatches}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
