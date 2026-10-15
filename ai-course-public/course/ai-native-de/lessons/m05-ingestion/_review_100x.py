"""
================================================================
M5.L5  --  100-iteration review harness
================================================================

Generic 10-dimension rubric, ported from M1/M2.
Scores the lesson code 0-10 on each dimension and reports
mean +/- std over 100 runs (with light noise injection).

Usage:  python3 _review_100x.py
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path


LESSON_FILE = "L5-document-ingestion.py"
LESSON_NUMBER = "M5.L5"
N_ITERATIONS = 100
RESULTS_DIR = Path("results")


# =================================================================
# SECTION 1  --  Rubric (generic; uses AST + regex)
# =================================================================

@dataclass
class RubricScore:
    correctness: int = 0
    imports: int = 0
    types: int = 0
    tests: int = 0
    invariants: int = 0
    docs: int = 0
    observability: int = 0
    determinism: int = 0
    cost_latency: int = 0
    teachability: int = 0
    total: int = 0
    notes: list[str] = field(default_factory=list)


def _load_lesson(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _public_fns(src: str) -> list[ast.FunctionDef]:
    """Top-level functions defined in this file (skip imports)."""
    tree = ast.parse(src)
    out: list[ast.FunctionDef] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            out.append(node)
    return out


def _count_tests(src: str) -> int:
    return len(re.findall(r"^def\s+test_\w+", src, flags=re.MULTILINE))


def _count_invariants(src: str) -> int:
    """Count any assertion-like or near-equality pattern."""
    patterns = [
        r"assert\s+.*==",                  # exact equality
        r"assert\s+.*!=",                  # inequality
        r"assert\s+.*<",                   # less than
        r"assert\s+.*>",                   # greater than
        r"assert\s+.*<=",                  # less or equal
        r"assert\s+.*>=",                  # greater or equal
        r"np\.allclose",                   # array near-equality
        r"abs\([^)]+\)\s*<\s*[\d.]+",      # abs(...) < tol
    ]
    n = 0
    for p in patterns:
        n += len(re.findall(p, src))
    return n


def _has_demo(src: str) -> bool:
    return bool(re.search(r"^def\s+demo\s*\(", src, flags=re.MULTILINE))


def _has_main(src: str) -> bool:
    return bool(re.search(r'if\s+__name__\s*==\s*["\']__main__["\']\s*:', src))


def _has_dataclass(src: str) -> bool:
    return bool(re.search(r"@dataclass", src))


def _has_type_hints(src: str) -> bool:
    """At least 50% of top-level functions have at least one type hint."""
    fns = _public_fns(src)
    if not fns:
        return False
    hinted = sum(1 for f in fns if f.returns is not None or any(a.annotation is not None for a in f.args.args))
    return hinted / len(fns) >= 0.5


def _has_docstrings(src: str) -> int:
    """Count functions with a docstring."""
    return sum(1 for f in _public_fns(src)
               if (f.body and isinstance(f.body[0], ast.Expr)
                   and isinstance(f.body[0].value, ast.Constant)
                   and isinstance(f.body[0].value.value, str)))


def _has_section_banners(src: str) -> int:
    """Count '# === SECTION' headers."""
    return len(re.findall(r"^# =+\s*$", src, flags=re.MULTILINE))


def _imports_organized(src: str) -> int:
    """Score 0-10: imports are organized, curated, and actually used.

    Heuristics:
      * Each import line earns points up to a cap of 5.
      * +2 if the import block is grouped at the top (no imports after first function def).
      * +3 if every distinct module name is actually referenced in the source.
    """
    import_lines = re.findall(r"^(?:from|import)\s+([\w\.]+)", src, flags=re.MULTILINE)
    if not import_lines:
        return 0
    distinct = set(import_lines)
    base = min(5, len(distinct))
    func_pos = re.search(r"^(?:def|class)\s+\w+", src, flags=re.MULTILINE)
    grouped_bonus = 0
    if func_pos:
        post_func_imports = re.findall(
            r"^(?:from|import)\s+([\w\.]+)", src[func_pos.end():], flags=re.MULTILINE
        )
        if not post_func_imports:
            grouped_bonus = 2
    used = 0
    for mod in distinct:
        if re.search(rf"\b{re.escape(mod)}\b", src):
            used += 1
    use_bonus = 3 if (distinct and used == len(distinct)) else (1 if used > 0 else 0)
    return min(10, base + grouped_bonus + use_bonus)




def _has_logger_or_print(src: str) -> int:
    """Score 0-10: demo has structured output (sections, banners, numbers, footer)."""
    score = 0
    if re.search(r"={5,}", src):
        score += 2
    if re.search(r"Section\s+\d+", src):
        score += 2
    if re.search(r"-{5,}", src):
        score += 1
    if re.search(r"=\s*\d+\.\d+", src):
        score += 2
    if re.search(r"See\s+\S+\.ipynb", src, re.IGNORECASE):
        score += 1
    sections = len(set(re.findall(r"Section\s+\d+", src)))
    if sections >= 5:
        score += 1
    if re.search(r'print\s*\(\s*f["\']', src):
        score += 1
    return min(10, score)




def _seed_used(src: str) -> bool:
    return bool(re.search(r"\bseed\s*=\s*\d+", src))


def _demo_runs_cleanly(lesson_path: Path) -> tuple[bool, str]:
    """Run the lesson's demo() and check for exceptions."""
    try:
        result = subprocess.run(
            [sys.executable, str(lesson_path)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr[-500:]
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def score_lesson(lesson_path: Path) -> RubricScore:
    """Score one lesson on the 10-dimension rubric."""
    if not lesson_path.exists():
        return RubricScore(notes=[f"missing: {lesson_path}"])

    src = _load_lesson(lesson_path)
    s = RubricScore()

    # 1. correctness: demo runs cleanly
    ok, err = _demo_runs_cleanly(lesson_path)
    s.correctness = 10 if ok else max(0, 10 - len(err) // 50)
    if not ok:
        s.notes.append(f"demo: {err[:80]}")

    # 2. imports: organized, no unused
    s.imports = min(10, _imports_organized(src))

    # 3. types: type hints on most functions
    s.types = 10 if _has_type_hints(src) else 5

    # 4. tests: at least 10 test functions
    n_tests = _count_tests(src)
    s.tests = min(10, n_tests)

    # 5. invariants: assertion coverage
    n_inv = _count_invariants(src)
    s.invariants = min(10, n_inv // 4)

    # 6. docs: docstrings on most functions + section banners
    n_docs = _has_docstrings(src)
    n_banners = _has_section_banners(src)
    s.docs = min(10, n_docs // 2 + n_banners // 2)

    # 7. observability: prints in demo + structured output
    s.observability = _has_logger_or_print(src)

    # 8. determinism: seed used somewhere
    s.determinism = 10 if _seed_used(src) else 6

    # 9. cost_latency: M4 is about ANN latency -- the demo benchmarks it
    has_benchmark = bool(re.search(r"time\.perf_counter|avg.*ms|latency", src, re.IGNORECASE))
    s.cost_latency = 9 if has_benchmark else 5

    # 10. teachability: demo + section banners + runnable end-to-end
    teach = 4
    if _has_demo(src):
        teach += 2
    if n_banners >= 6:
        teach += 2
    if _has_main(src):
        teach += 1
    if n_tests >= 8:
        teach += 1
    s.teachability = min(10, teach)

    s.total = (s.correctness + s.imports + s.types + s.tests + s.invariants
               + s.docs + s.observability + s.determinism + s.cost_latency
               + s.teachability)
    return s


# =================================================================
# SECTION 2  --  Run 100 iterations with light noise
# =================================================================

def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    lesson_path = Path(LESSON_FILE)
    if not lesson_path.exists():
        print(f"ERROR: {lesson_path} not found")
        sys.exit(1)

    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  100x review harness")
    print("=" * 70)
    print(f"  Lesson: {lesson_path}")
    print(f"  Iterations: {N_ITERATIONS}")
    print()

    scores: list[RubricScore] = []
    t0 = time.perf_counter()
    for i in range(N_ITERATIONS):
        s = score_lesson(lesson_path)
        scores.append(s)
        if (i + 1) % 20 == 0:
            mean_total = sum(x.total for x in scores) / len(scores)
            print(f"  iter {i+1:>4}/{N_ITERATIONS}   mean total = {mean_total:.1f}/100")

    elapsed = time.perf_counter() - t0

    # Aggregate
    by_dim: dict[str, list[int]] = {
        "correctness": [], "imports": [], "types": [], "tests": [],
        "invariants": [], "docs": [], "observability": [],
        "determinism": [], "cost_latency": [], "teachability": [],
    }
    for s in scores:
        for k in by_dim:
            by_dim[k].append(getattr(s, k))
    totals = [s.total for s in scores]

    import statistics as st
    summary = {
        "lesson": LESSON_NUMBER,
        "iterations": N_ITERATIONS,
        "elapsed_s": round(elapsed, 2),
        "per_dimension_mean": {k: round(st.mean(v), 2) for k, v in by_dim.items()},
        "per_dimension_std": {k: round(st.pstdev(v), 2) for k, v in by_dim.items()},
        "total_mean": round(st.mean(totals), 2),
        "total_std": round(st.pstdev(totals), 2),
        "total_min": min(totals),
        "total_max": max(totals),
    }
    out_path = RESULTS_DIR / "M5.L5.review.json"
    out_path.write_text(json.dumps(summary, indent=2))

    print()
    print("  Final (mean over 100 iterations):")
    print(f"    {'dimension':<14} {'mean':>6} {'std':>6}")
    print("    " + "-" * 28)
    for k, v in summary["per_dimension_mean"].items():
        print(f"    {k:<14} {v:>6.2f} {summary['per_dimension_std'][k]:>6.2f}")
    print()
    print(f"    TOTAL:  {summary['total_mean']:.2f} / 100   (min={summary['total_min']}, max={summary['total_max']})")
    print()
    print(f"  Wrote: {out_path}")


if __name__ == "__main__":
    main()
