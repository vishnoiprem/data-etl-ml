"""
nb_helpers/transform_notebook.py — Rewrite a notebook to use rich-display helpers.

Strategy:
  1. Add an import cell at the very top (before any other code).
  2. For each existing code cell, convert print() calls to display_* calls:
       print("📧 Read ...")          -> display_box("...", kind="info")
       print(f"📦 Loaded {n} ...")   -> display_box(f"...", kind="success")
       print("PASS")                -> display_status("PASS", kind="pass")
       print(f"Error: ...")         -> display_box("...", kind="danger")
       print(json.dumps({...}))     -> display_json({...})
  3. Re-execute the notebook to populate outputs.

Usage:
    python3 nb_helpers/transform_notebook.py path/to/notebook.ipynb
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

NB_HELPERS_IMPORT = '''# --- Rich display helpers (added by transform_notebook.py) ---
import sys
from pathlib import Path
_HELPERS = None
# Search up the directory tree from THIS notebook's location, not just cwd
_this_nb = globals().get("__vsc_ipynb_file__") or globals().get("__file__")
_candidates = [Path.cwd()]
if _this_nb:
    _candidates.append(Path(_this_nb).resolve().parent)
for _p in _candidates:
    for _anc in [_p, *_p.parents]:
        if (_anc / "nb_helpers" / "rich_display.py").exists():
            _HELPERS = _anc
            break
    if _HELPERS:
        break
if _HELPERS is None:
    raise ImportError(
        "Could not locate nb_helpers/ — make sure you're running this "
        "notebook from inside the ai-course-public/ checkout."
    )
sys.path.insert(0, str(_HELPERS))
from nb_helpers import (
    display_h1, display_h2, display_h3, display_p,
    display_box, display_kv, display_table, display_json,
    display_status, display_divider, display_banner, display_step,
)
'''


def detect_kind(text: str) -> str:
    """Heuristically detect the kind of a print() call from its content."""
    t = text.lower()
    if any(x in t for x in ("❌", "error", "failed", "exception", "traceback", "not found")):
        return "danger"
    if any(x in t for x in ("⚠️", "warning", "caution", "deprecated")):
        return "warning"
    if any(x in t for x in ("✅", "✓", "pass", "success", "ok", "loaded", "found")):
        return "success"
    if any(x in t for x in ("📝", "note", "tip", "💡")):
        return "note"
    return "info"


def detect_emoji(text: str) -> str | None:
    """Extract leading emoji if present."""
    m = re.match(r"^(\W*)([\\U0001F300-\\U0001FAFF\\U00002600-\\U000027BF]+)", text)
    if m:
        return m.group(2)
    return None


def transform_print_call(line: str) -> str | None:
    """Convert a single print() line. Return None if it should be removed.

    Preserves leading indentation and trailing comments.

    Heuristics:
      - print() (no args)                                        -> display_divider() (blank line)
      - print("=== " * n) / print("=" * n)                       -> display_divider()
      - print("PASS") / print("FAIL")                            -> display_status(...)
      - print(json.dumps(obj, ...))                              -> display_json(obj)
      - print("label:", value)                                   -> display_kv({...}) or display_box
      - print(f"emoji: {var}") with f-string + method call       -> display_box(..., kind=...)
      - print("any other text")                                  -> display_box(..., kind=...)
    """
    # Preserve leading whitespace
    indent_match = re.match(r'^(\s*)', line)
    indent = indent_match.group(1) if indent_match else ""
    # Strip a trailing comment (# ...) for matching but keep it for the return
    code_part = line
    comment_part = ""
    hash_idx = line.find('#')
    if hash_idx >= 0:
        # Make sure the # is not inside a string — for simplicity, assume no # inside strings
        code_part = line[:hash_idx].rstrip()
        comment_part = "  " + line[hash_idx:]

    stripped = code_part.strip()

    # Empty print() -> blank line (rendered as divider)
    if re.match(r'^print\s*\(\s*\)\s*$', stripped):
        return f"{indent}display_divider()"

    # Divider lines: print("=" * 60) or print("---" * 30)
    if re.match(r'^print\s*\(\s*[\'"]([=\-*_~·\.]{3,})[\'"]\s*\*\s*\d+\s*\)\s*$', stripped):
        return f"{indent}display_divider()"

    # Status: print("PASS") or print("FAIL") or print("OK")
    m = re.match(r'^print\s*\(\s*[\'"]([A-Z][A-Z _]{1,20})[\'"]\s*\)\s*$', stripped)
    if m:
        word = m.group(1).strip()
        if word in ("PASS", "OK", "SUCCESS", "DONE"):
            return f'{indent}display_status("{word}", kind="success"){comment_part}'
        if word in ("FAIL", "ERROR", "FAILED"):
            return f'{indent}display_status("{word}", kind="danger"){comment_part}'
        if word in ("WARN", "WARNING"):
            return f'{indent}display_status("{word}", kind="warning"){comment_part}'

    # JSON: print(json.dumps(obj, indent=2)) or print(json.dumps(obj))
    m = re.match(
        r'^print\s*\(\s*json\.dumps\s*\(\s*([A-Za-z_][\w\.]*)\s*(?:,\s*[^)]+)?\s*\)\s*\)\s*$',
        stripped,
    )
    if m:
        var = m.group(1)
        return f"{indent}display_json({var}){comment_part}"

    # f-string with method calls: print(f"📦 Loaded {len(x)}.")
    m = re.match(
        r'^print\s*\(\s*f?[\'"](.+?)[\'"]\s*(?:\*\s*[\d]+\s*)?\)\s*$',
        stripped,
    )
    if m:
        body = m.group(1)
        # decode common escapes — f-string prefix
        if body.startswith(("f'", 'f"')):
            body = body[2:-1]
        # detect kind
        kind = detect_kind(body)
        mono = any(c in body for c in ("┌", "─", "│", "└", "├", "┤", "┘", "┐", "█", "▓", "▒", "|"))
        if mono:
            return f'{indent}display_box({repr(body)}, kind="{kind}", mono=True){comment_part}'
        return f'{indent}display_box({repr(body)}, kind="{kind}"){comment_part}'

    # print with expression (variable only, not a literal)
    m = re.match(r'^print\s*\(\s*([A-Za-z_][\w\.]*)\s*\)\s*$', stripped)
    if m:
        var = m.group(1)
        return f"{indent}display({var}){comment_part}"

    return None  # leave as-is


def transform_code_cell(src: str) -> str:
    """Transform a code cell's source. Mutates the print() lines."""
    lines = src.split("\n")
    out = []
    skip_next_blank = False
    for line in lines:
        transformed = transform_print_call(line)
        if transformed is None:
            out.append(line)
        else:
            out.append(transformed)
            skip_next_blank = False
    return "\n".join(out)


def inject_helper_import(nb: dict) -> None:
    """Insert the import cell as the first code cell (after any leading markdown)."""
    # Find first code cell index
    first_code = 0
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] == "code":
            first_code = i
            break
    # Build new cell
    new_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [NB_HELPERS_IMPORT],
    }
    nb["cells"].insert(first_code, new_cell)


def transform_notebook_inplace(path: Path) -> None:
    """Transform a single notebook in place."""
    nb = json.loads(path.read_text(encoding="utf-8"))
    # 1. Inject the import cell
    inject_helper_import(nb)
    # 2. Transform all OTHER code cells (skip the just-injected one)
    for c in nb["cells"][1:]:
        if c["cell_type"] == "code":
            src = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
            new_src = transform_code_cell(src)
            c["source"] = new_src.splitlines(keepends=True)
            if c["source"] and not c["source"][-1].endswith("\n"):
                c["source"][-1] += "\n"
    # 3. Clear all existing outputs (so re-execution regenerates them)
    for c in nb["cells"]:
        if c["cell_type"] == "code":
            c["outputs"] = []
            c["execution_count"] = None
    path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("Usage: transform_notebook.py <notebook.ipynb> [more.ipynb ...]")
        sys.exit(1)
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"  SKIP: {p} (not found)")
            continue
        print(f"  TRANSFORM: {p}")
        transform_notebook_inplace(p)
    print("Done.")


if __name__ == "__main__":
    main()
