"""Run a Beam lab and capture stdout/stderr to a file, so failures are visible."""

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
INTERP = str(HERE.parent / ".beam-venv" / "bin" / "python")


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else "labs/01-beam-basics.py"
    script = HERE / target
    result = subprocess.run(
        [INTERP, str(script)],
        capture_output=True,
        text=True,
        cwd=str(HERE),
    )
    out = HERE / "_last_run.txt"
    out.write_text(
        f"=== exit {result.returncode} ===\n"
        f"=== STDOUT ===\n{result.stdout}\n"
        f"=== STDERR ===\n{result.stderr[-4000:]}\n"
    )
    print(out)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
