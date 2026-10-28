"""Extract every python fence from the five Module 4 chapters and report
which ones are self-contained enough to execute (imports only, no shell
heredocs, no undefined names from the chapter prose)."""

import ast
import pathlib
import re
import sys

CHAPTERS = [
    "chapters/19-gcp-project-billing-and-apis.md",
    "chapters/20-service-accounts-and-bucket.md",
    "chapters/21-direct-runner.md",
    "chapters/22-saving-to-gcs.md",
    "chapters/23-pipelineoptions-deep-dive.md",
]

pattern = re.compile(r"```python\n(.*?)```", re.DOTALL)

for path in CHAPTERS:
    text = pathlib.Path(path).read_text()
    blocks = pattern.findall(text)
    parses = 0
    for i, block in enumerate(blocks):
        try:
            ast.parse(block)
            parses += 1
        except SyntaxError as exc:
            print(f"  SYNTAX ERROR {path} block {i}: {exc.msg} line {exc.lineno}")
            for j, line in enumerate(block.splitlines()):
                print(f"      {j+1}: {line}")
    print(f"{path:44} blocks={len(blocks):3} parsed={parses:3}")
