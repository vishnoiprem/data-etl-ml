"""Execute a notebook with nbconvert and report the outcome."""
import subprocess
import sys

nb = sys.argv[1]
out = sys.argv[2]
proc = subprocess.run(
    [".venv/bin/python", "-m", "jupyter", "nbconvert", "--to", "notebook",
     "--execute", "--output", out, nb],
    capture_output=True, text=True,
)
print("returncode:", proc.returncode)
print("--- stdout tail ---")
print("\n".join(proc.stdout.splitlines()[-25:]))
print("--- stderr tail ---")
print("\n".join(proc.stderr.splitlines()[-40:]))
sys.exit(proc.returncode)
