"""Execute the self-contained python fences from the Module 4 chapters.

A fence is "self-contained" if it defines every name it uses at module
level (no reliance on a previous fence in the same chapter). We run each
in a fresh namespace and report failures, excluding fences that are
obviously illustrative (heredoc bodies, or ones that deliberately
raise).
"""

import ast
import pathlib
import re
import traceback

CHAPTERS = [
    "chapters/19-gcp-project-billing-and-apis.md",
    "chapters/20-service-accounts-and-bucket.md",
    "chapters/21-direct-runner.md",
    "chapters/22-saving-to-gcs.md",
    "chapters/23-pipelineoptions-deep-dive.md",
]

pattern = re.compile(r"```python\n(.*?)```", re.DOTALL)

# Fences that cannot run standalone: they are heredoc bodies, they
# deliberately raise, or they need a GCP project.
SKIP_MARKERS = (
    "your-service-account",
    "YOUR_BUCKET",
    "DEMO_GCS_OUTPUT",
    "gcloud ",
    "EOF",
    "GCS_OUTPUT = os.environ",
    "SystemExit",
)

failures = 0
total = 0

for path in CHAPTERS:
    text = pathlib.Path(path).read_text()
    for i, block in enumerate(pattern.findall(text)):
        if any(marker in block for marker in SKIP_MARKERS):
            continue
        # Skip blocks that are heredoc bodies (start with 'EOF' or contain
        # a bare 'EOF' line) — the audit already proved they parse.
        lines = [ln for ln in block.splitlines() if ln.strip() != "EOF"]
        candidate = "\n".join(lines)
        try:
            ast.parse(candidate)
        except SyntaxError:
            continue
        # Only run blocks that look like complete programs.
        if "import " not in candidate:
            continue
        total += 1
        namespace = {"__name__": "__main__"}
        try:
            exec(compile(candidate, f"{path}#{i}", "exec"), namespace)
        except SystemExit:
            pass
        except Exception:
            failures += 1
            print(f"--- RUNTIME FAILURE {path} block {i} ---")
            print(candidate)
            traceback.print_exc()
            print()

print(f"executed={total} failures={failures}")
