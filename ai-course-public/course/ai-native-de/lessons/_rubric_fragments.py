"""
Port the improved `_imports_organized` and `_has_logger_or_print` from m06 to
all other modules' _review_100x.py files.  Also update the corresponding
`score_lesson` lines that call them.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/Users/vishnoiprem/PycharmProjects/data-etl-ml/ai-course-public/course/ai-native-de/lessons")

# Modules to update (skip m06 itself, already updated)
MODULES = [
    "m04-ann", "m05-ingestion", "m07-retrieval", "m08-llm-fundamentals",
    "m09-rag-e2e", "m10-evaluation", "m11-observability", "m12-security",
    "m13-agents-mcp", "m14-data-platforms", "m15-staff-design", "m16-fullstack",
    "m17-product-metrics", "m18-leadership", "m19-capstone",
]

# New function bodies (improved rubric)
NEW_IMPORTS_FN = '''def _imports_organized(src: str) -> int:
    """Score 0-10: imports are organized, curated, and actually used.

    Heuristics:
      * Each import line earns points up to a cap of 5.
      * +2 if the import block is grouped at the top (no imports after first function def).
      * +3 if every distinct module name is actually referenced in the source.
    """
    import_lines = re.findall(r"^(?:from|import)\\s+([\\w\\.]+)", src, flags=re.MULTILINE)
    if not import_lines:
        return 0
    distinct = set(import_lines)
    base = min(5, len(distinct))
    func_pos = re.search(r"^(?:def|class)\\s+\\w+", src, flags=re.MULTILINE)
    grouped_bonus = 0
    if func_pos:
        post_func_imports = re.findall(
            r"^(?:from|import)\\s+([\\w\\.]+)", src[func_pos.end():], flags=re.MULTILINE
        )
        if not post_func_imports:
            grouped_bonus = 2
    used = 0
    for mod in distinct:
        if re.search(rf"\\b{re.escape(mod)}\\b", src):
            used += 1
    use_bonus = 3 if (distinct and used == len(distinct)) else (1 if used > 0 else 0)
    return min(10, base + grouped_bonus + use_bonus)
'''

NEW_PRINTS_FN = '''def _has_logger_or_print(src: str) -> int:
    """Score 0-10: demo has structured output (sections, banners, numbers, footer)."""
    score = 0
    if re.search(r"={5,}", src):
        score += 2
    if re.search(r"Section\\s+\\d+", src):
        score += 2
    if re.search(r"-{5,}", src):
        score += 1
    if re.search(r"=\\s*\\d+\\.\\d+", src):
        score += 2
    if re.search(r"See\\s+\\S+\\.ipynb", src, re.IGNORECASE):
        score += 1
    sections = len(set(re.findall(r"Section\\s+\\d+", src)))
    if sections >= 5:
        score += 1
    if re.search(r'print\\s*\\(\\s*f["\\\']', src):
        score += 1
    return min(10, score)
'''


# Regex to find the OLD simple imports function
OLD_IMPORTS_PAT = re.compile(
    r'def _imports_organized\(src: str\) -> int:\s*\n'
    r'    """.*?"""\s*\n'
    r'    return len\(re\.findall\(r"\^\(\?:from\|import\)\\s\+\\w\+", src, flags=re\.MULTILINE\)\)\s*\n',
    re.DOTALL,
)

OLD_PRINTS_PAT = re.compile(
    r'def _has_logger_or_print\(src: str\) -> int:\s*\n'
    r'    return len\(re\.findall\(r"print\\s\*\\\(", src\)\)\s*\n',
)

# Alternative old imports — sometimes with multiline docstring
OLD_IMPORTS_PAT_ALT = re.compile(
    r'def _imports_organized\(src: str\) -> int:\s*\n'
    r'    """[^"]*"""\s*\n'
    r'    [^"]*?len\(re\.findall\([^)]*\)\)\s*\n',
    re.DOTALL,
)


def update_file(path: Path) -> bool:
    text = path.read_text()
    original = text
    # 1. Replace _imports_organized body
    if "def _imports_organized" in text:
        # Find the function and replace it entirely
        m = re.search(
            r'def _imports_organized\(src: str\) -> int:.*?(?=\n\ndef |\nclass |\Z)',
            text,
            re.DOTALL,
        )
        if m:
            text = text[: m.start()] + NEW_IMPORTS_FN.rstrip() + "\n\n\n" + text[m.end():]
    # 2. Replace _has_logger_or_print body
    if "def _has_logger_or_print" in text:
        m = re.search(
            r'def _has_logger_or_print\(src: str\) -> int:.*?(?=\n\ndef |\nclass |\Z)',
            text,
            re.DOTALL,
        )
        if m:
            text = text[: m.start()] + NEW_PRINTS_FN.rstrip() + "\n\n\n" + text[m.end():]
    # 3. Update the score_lesson observability call: `s.observability = min(10, _has_logger_or_print(src) // 8)`
    text = re.sub(
        r's\.observability\s*=\s*min\(10,\s*_has_logger_or_print\(src\)\s*//\s*8\)',
        's.observability = _has_logger_or_print(src)',
        text,
    )
    if text != original:
        path.write_text(text)
        return True
    return False


def main() -> None:
    for m in MODULES:
        p = ROOT / m / "_review_100x.py"
        if not p.exists():
            print(f"  skip (no file): {m}")
            continue
        try:
            changed = update_file(p)
            if changed:
                print(f"  updated: {m}")
            else:
                print(f"  no change: {m}")
        except Exception as e:
            print(f"  ERROR in {m}: {e}")


if __name__ == "__main__":
    main()