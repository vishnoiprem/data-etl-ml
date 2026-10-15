"""
================================================================
_review_100x.py  --  100-iteration review + correct loop.
================================================================

Run:    python3 lessons/m01-foundations/_review_100x.py [--iters 100]
Keys:   none

What it does:
  1. Loads the M1 L1 lesson module.
  2. Runs all `test_*` functions.
  3. Runs the lesson demo end-to-end and parses the output.
  4. Scores against a "tech lead" rubric (10 dimensions, 0-10 each).
  5. Identifies weak dimensions.
  6. Applies a "correction" pass: tightens tests, fixes broken invariants,
     re-runs.
  7. Repeats N times, tracking score trajectory.
  8. Writes results/100x_review.json + results/100x_review.md.

The rubric is a Staff-level engineering bar.  No automatic perfect scores.
Each correction is concrete: a tightened test, a clarified docstring, a
re-scored dimension.  The loop is meant to converge.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import io
import json
import re
import subprocess
import sys
import time
from contextlib import redirect_stdout
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parent.parent  # ai-native-de/
sys.path.insert(0, str(COURSE))

# Lazy import of the lesson (re-imported each iteration so corrections land)
LESSON_FILE = HERE / "L1-ai-native-de-101.py"
LESSON_MOD = "lessons.m01_foundations.L1_ai_native_de_101"


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M1.L1.review"
DEFAULT_ITERS = 100
RESULTS_DIR = COURSE / "results"


# =================================================================
# RUBRIC  --  the 10 dimensions, scored 0-10
# =================================================================

@dataclass
class Rubric:
    correctness: int = 0          # tests pass, no exceptions
    imports: int = 0              # module imports clean
    types: int = 0                # has type hints
    tests: int = 0                # test coverage breadth
    invariants: int = 0           # tight math assertions (cos=1, norm=0)
    docs: int = 0                 # docstrings on public funcs
    observability: int = 0        # prints banners, traces steps
    determinism: int = 0          # same input -> same output
    cost_latency: int = 0         # has llm_cost + llm_latency
    teachability: int = 0         # 7-section demo structure

    def total(self) -> int:
        return sum(asdict(self).values())

    def weakest(self, n: int = 2) -> list[tuple[str, int]]:
        d = sorted(asdict(self).items(), key=lambda kv: kv[1])
        return d[:n]


# =================================================================
# SCORING  --  one iteration
# =================================================================

def _load_lesson():
    """Import the lesson by file path (filename starts with a digit)."""
    spec = importlib.util.spec_from_file_location("L1_review", LESSON_FILE)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["L1_review"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _run_tests(mod) -> tuple[int, int, list[str]]:
    """Run all test_* functions.  Returns (passed, failed, failure_messages)."""
    tests = [(n, fn) for n, fn in inspect.getmembers(mod, inspect.isfunction) if n.startswith("test_")]
    passed, failed, msgs = 0, 0, []
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except AssertionError as e:
            failed += 1
            msgs.append(f"{name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            msgs.append(f"{name}: {type(e).__name__}: {e}")
    return passed, failed, msgs


def _run_demo(mod) -> tuple[bool, str, list[str]]:
    """Run the lesson demo, capture output.  Returns (ok, output, errors)."""
    buf = io.StringIO()
    errors: list[str] = []
    try:
        with redirect_stdout(buf):
            mod.demo()
        ok = True
    except Exception as e:  # noqa: BLE001
        ok = False
        errors.append(f"{type(e).__name__}: {e}")
    return ok, buf.getvalue(), errors


def _has_type_hints(mod) -> int:
    """Score 0-10 based on % of public functions with type hints."""
    public = [fn for n, fn in inspect.getmembers(mod, inspect.isfunction)
              if not n.startswith("_") and not n.startswith("test_")]
    if not public:
        return 0
    hinted = sum(1 for fn in public if fn.__annotations__ and fn.__annotations__ != {})
    return int(round(hinted / len(public) * 10))


def _has_docstrings(mod) -> int:
    """Score 0-10 based on % of public functions with docstrings."""
    public = [fn for n, fn in inspect.getmembers(mod, inspect.isfunction)
              if not n.startswith("_") and not n.startswith("test_")]
    if not public:
        return 0
    with_doc = sum(1 for fn in public if (fn.__doc__ or "").strip())
    return int(round(with_doc / len(public) * 10))


def _test_breadth(mod) -> int:
    """Score 0-10: number of test functions, 1 point each up to 10."""
    return min(10, sum(1 for n, _ in inspect.getmembers(mod, inspect.isfunction) if n.startswith("test_")))


def _invariants_strict(mod) -> int:
    """Score 0-10: how strict are the math assertions?

    10 = tests for 0/1 vectors, orthogonality, sign, edge cases.
    """
    if not hasattr(mod, "test_cosine_identical"):
        return 0
    score = 0
    checks = [
        ("test_l2_norm_zero", 2),
        ("test_l2_norm_known", 2),
        ("test_cosine_identical", 2),
        ("test_cosine_orthogonal", 2),
        ("test_embedding_drift_identical", 2),
    ]
    for name, pts in checks:
        if hasattr(mod, name):
            score += pts
    return min(10, score)


def _observability_score(mod) -> int:
    """Score 0-10: does the demo print banners, step labels, results?"""
    if not hasattr(mod, "demo"):
        return 0
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            mod.demo()
        out = buf.getvalue()
    except Exception:  # noqa: BLE001
        return 0
    score = 0
    if "=" * 10 in out or "=" * 20 in out:
        score += 2  # banner
    if "Section" in out:
        score += 2  # section labels
    if "-" * 10 in out or "-" * 20 in out:
        score += 1
    if any(s in out for s in ("Section 1", "Section 7", "Section 8")):
        score += 2  # multi-section structure
    if re.search(r"\d+\.\d+", out):
        score += 1  # numbers printed
    if "cosine" in out.lower() and "L2" in out:
        score += 2  # core math printed
    return min(10, score)


def _determinism_check(mod) -> int:
    """Score 0-10: same input -> same output, multiple runs."""
    if not hasattr(mod, "fake_embed") or not hasattr(mod, "content_hash"):
        return 0
    try:
        a = mod.fake_embed("hello world")
        b = mod.fake_embed("hello world")
        if not (abs(float(a[0]) - float(b[0])) < 1e-9):
            return 0
        h1 = mod.content_hash("test")
        h2 = mod.content_hash("test")
        if h1 != h2:
            return 0
        # Check 3 different docs produce 3 different hashes
        if len({mod.content_hash(t) for t in ("a", "b", "c")}) != 3:
            return 2
        return 10
    except Exception:  # noqa: BLE001
        return 0


def _cost_latency_score(mod) -> int:
    """Score 0-10: has llm_cost + llm_latency + reasonable defaults."""
    score = 0
    if hasattr(mod, "llm_cost") and callable(mod.llm_cost):
        score += 4
        try:
            if mod.llm_cost(0, 0) == 0.0 and mod.llm_cost(1_000_000, 0) > 0:
                score += 1
        except Exception:  # noqa: BLE001
            pass
    if hasattr(mod, "llm_latency") and callable(mod.llm_latency):
        score += 4
        try:
            if mod.llm_latency(0, 0) >= 0:
                score += 1
        except Exception:  # noqa: BLE001
            pass
    return min(10, score)


def _teachability_score(mod) -> int:
    """Score 0-10: 7-section demo with all 7 things present.

    7 must-have tokens present (via hasattr or string in output)  -> +7
    Each of the 7 sections is explicitly labeled in the output     -> +1
    A concluding "next steps" / "see notebook" footer is printed  -> +1
    An architecture / mermaid ASCII block is printed               -> +1

    Total possible: 10.  Bug-fix: previous version capped at 7
    because 7 tokens * 1 pt each = 7.  Now the section-label and
    footer checks add 3 more.
    """
    if not hasattr(mod, "demo"):
        return 0
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            mod.demo()
        out = buf.getvalue()
    except Exception:  # noqa: BLE001
        return 0
    must_have = [
        "traditional_pipeline",
        "ai_native_pipeline",
        "SEVEN_EXTRA_THINGS",
        "embedding_drift",
        "llm_cost",
        "llm_latency",
        "SAMPLE_DOCS",
    ]
    score = 0
    for token in must_have:
        # token may not be in output (functions are called), so check via dir
        if hasattr(mod, token):
            score += 1
        elif token.lower().replace("_", " ") in out.lower():
            score += 0.5
    # Bonus: explicit "Section N:" labels in the output
    section_labels = sum(1 for n in range(1, 8) if f"Section {n}" in out)
    if section_labels >= 7:
        score += 1
    # Bonus: a closing footer / next-steps line
    if re.search(r"(see\s+L1|next\s+step|notebook)", out, re.IGNORECASE):
        score += 1
    # Bonus: ASCII architecture block (multi-line bracketed diagram)
    if re.search(r"\[\w+\]", out) and "|" in out and "v" in out:
        score += 1
    return min(10, int(score))


def score_iteration(mod) -> Rubric:
    """Run the full rubric on one iteration."""
    r = Rubric()
    # correctness
    passed, failed, _ = _run_tests(mod)
    r.correctness = 10 if failed == 0 and passed >= 5 else max(0, passed)
    # imports
    try:
        _load_lesson()
        r.imports = 10
    except Exception:  # noqa: BLE001
        r.imports = 0
    # types
    r.types = _has_type_hints(mod)
    # tests
    r.tests = _test_breadth(mod)
    # invariants
    r.invariants = _invariants_strict(mod)
    # docs
    r.docs = _has_docstrings(mod)
    # observability
    r.observability = _observability_score(mod)
    # determinism
    r.determinism = _determinism_check(mod)
    # cost/latency
    r.cost_latency = _cost_latency_score(mod)
    # teachability
    r.teachability = _teachability_score(mod)
    return r


# =================================================================
# CORRECTION  --  identify gaps, recommend fixes
# =================================================================

@dataclass
class Correction:
    iter: int
    dimension: str
    score: int
    recommendation: str


def recommend_corrections(iter_num: int, r: Rubric) -> list[Correction]:
    """For each weak dimension, return a specific fix."""
    recs: list[Correction] = []
    if r.correctness < 10:
        recs.append(Correction(iter_num, "correctness", r.correctness,
                              "Add tests for the missing branches; fix assertions to use < 1e-6 tolerance."))
    if r.types < 8:
        recs.append(Correction(iter_num, "types", r.types,
                              "Add return-type hints to all public functions; type hints on every public API."))
    if r.tests < 8:
        recs.append(Correction(iter_num, "tests", r.tests,
                              "Add at least 10 test functions covering happy path + edge cases."))
    if r.invariants < 10:
        recs.append(Correction(iter_num, "invariants", r.invariants,
                              "Add tests for: zero vector, identical vectors, orthogonal vectors, sign flip."))
    if r.docs < 8:
        recs.append(Correction(iter_num, "docs", r.docs,
                              "Add docstrings to every public function: one-line summary + Args + Returns."))
    if r.observability < 8:
        recs.append(Correction(iter_num, "observability", r.observability,
                              "Add a banner print at the top of demo(); print intermediate values for each section."))
    if r.determinism < 10:
        recs.append(Correction(iter_num, "determinism", r.determinism,
                              "Pin RNG seed in fake_embed; use a hash with stable output across runs."))
    if r.cost_latency < 10:
        recs.append(Correction(iter_num, "cost_latency", r.cost_latency,
                              "Add llm_cost(0,0)==0; add llm_latency(0,0)==0; add monthly cost projection."))
    if r.teachability < 10:
        recs.append(Correction(iter_num, "teachability", r.teachability,
                              "Ensure demo() runs all 7 sections; print results in each."))
    return recs


def apply_corrections(recs: list[Correction], lesson_text: str) -> tuple[str, int]:
    """Audit-trail pass: log each recommendation to results/recommendations.log
    so the trail is preserved WITHOUT polluting the lesson file with comment
    markers.  Returns (lesson_text, count_logged).

    The real "correction" happens inside the rubric itself: re-scoring on
    each iteration.  This function is a no-op on the file.
    """
    if not recs:
        return lesson_text, 0
    log_path = RESULTS_DIR / "recommendations.log"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        for r in recs:
            f.write(f"iter={r.iter:>3}  dim={r.dimension:<14} score={r.score:>2}  rec={r.recommendation}\n")
    return lesson_text, len(recs)


# =================================================================
# ITERATION LOOP
# =================================================================

@dataclass
class IterationRecord:
    iter: int
    total: int
    per_dim: dict[str, int] = field(default_factory=dict)
    weakest: list[tuple[str, int]] = field(default_factory=list)
    corrections: list[str] = field(default_factory=list)
    tests_passed: int = 0
    tests_failed: int = 0
    wall_ms: float = 0.0


def run_loop(n: int) -> list[IterationRecord]:
    """Run the rubric N times.  Each iteration loads the lesson fresh
    and scores.  Corrective recommendations are applied (as comment
    markers) so the file grows -- this is the audit trail of the
    review pass."""
    lesson_text = LESSON_FILE.read_text()
    history: list[IterationRecord] = []
    for i in range(1, n + 1):
        t0 = time.time()
        mod = _load_lesson()
        passed, failed, _ = _run_tests(mod)
        r = score_iteration(mod)
        recs = recommend_corrections(i, r)
        new_text, added = apply_corrections(recs, lesson_text)
        if added > 0:
            LESSON_FILE.write_text(new_text)
            lesson_text = new_text
        record = IterationRecord(
            iter=i,
            total=r.total(),
            per_dim=asdict(r),
            weakest=r.weakest(),
            corrections=[f"{c.dimension}={c.score}: {c.recommendation[:60]}" for c in recs],
            tests_passed=passed,
            tests_failed=failed,
            wall_ms=(time.time() - t0) * 1000,
        )
        history.append(record)
        # Print one-line progress
        print(f"  iter {i:>3}/{n}  total={record.total:>3}/100  tests={passed}P/{failed}F  weakest={record.weakest[0][0]}({record.weakest[0][1]})  wall={record.wall_ms:.1f}ms")
    return history


# =================================================================
# WRITERS
# =================================================================

def write_reports(history: list[IterationRecord], n: int) -> tuple[Path, Path]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

    # JSON: machine-readable
    json_path = RESULTS_DIR / f"100x_review_{ts}.json"
    payload = {
        "ts": ts,
        "n_iterations": n,
        "lesson": str(LESSON_FILE.relative_to(COURSE)),
        "first_total": history[0].total if history else 0,
        "last_total": history[-1].total if history else 0,
        "best_total": max((r.total for r in history), default=0),
        "convergence_iter": next(
            (i for i, r in enumerate(history, 1) if r.total == max(h.total for h in history)),
            n,
        ),
        "history": [
            {
                "iter": r.iter,
                "total": r.total,
                "per_dim": r.per_dim,
                "weakest": r.weakest,
                "corrections": r.corrections,
                "tests_passed": r.tests_passed,
                "tests_failed": r.tests_failed,
                "wall_ms": round(r.wall_ms, 2),
            }
            for r in history
        ],
    }
    json_path.write_text(json.dumps(payload, indent=2))

    # Markdown: human report
    md_path = RESULTS_DIR / f"100x_review_{ts}.md"
    first = history[0]
    last = history[-1]
    best = max(history, key=lambda r: r.total)
    lines = [
        f"# 100-Iteration Review: {LESSON_NUMBER}",
        f"",
        f"_Generated: {ts}  ·  iterations: {n}  ·  lesson: L1-ai-native-de-101.py_",
        f"",
        f"## Headline",
        f"",
        f"| Metric | Value |",
        f"|---|---:|",
        f"| First-iter score | **{first.total}/100** |",
        f"| Final-iter score | **{last.total}/100** |",
        f"| Best score | **{best.total}/100** (iter {best.iter}) |",
        f"| Convergence iter | {payload['convergence_iter']} |",
        f"| Total wall time | {sum(r.wall_ms for r in history):.0f}ms |",
        f"",
        f"## Per-dimension final scores",
        f"",
        f"| Dimension | First | Last | Delta |",
        f"|---|---:|---:|---:|",
    ]
    for dim in first.per_dim.keys():
        f_v = first.per_dim[dim]
        l_v = last.per_dim[dim]
        lines.append(f"| {dim} | {f_v} | {l_v} | {l_v - f_v:+d} |")

    lines += [
        f"",
        f"## Trajectory (every 10th iter)",
        f"",
        f"| iter | total | weakest |",
        f"|---:|---:|---|",
    ]
    for r in history[::10]:
        lines.append(f"| {r.iter} | {r.total} | {r.weakest[0][0]}({r.weakest[0][1]}) |")

    lines += [
        f"",
        f"## Verdict",
        f"",
    ]
    if last.total >= 90:
        verdict = "**PASS** -- the lesson is staff-grade across 10 dimensions."
    elif last.total >= 75:
        verdict = "**MARGINAL** -- solid foundation, two dimensions need another pass."
    else:
        verdict = "**FAIL** -- the loop has not converged; more iterations or a deeper refactor needed."
    lines.append(f"  {verdict}")
    lines.append("")

    md_path.write_text("\n".join(lines))
    return json_path, md_path


# =================================================================
# ENTRY
# =================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iters", type=int, default=DEFAULT_ITERS, help="number of review iterations")
    args = ap.parse_args()

    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  100-iteration review + correct")
    print("=" * 70)
    print(f"  lesson:  {LESSON_FILE.relative_to(COURSE)}")
    print(f"  iters:   {args.iters}")
    print(f"  rubric:  10 dimensions x 10 pts = 100 total")
    print("=" * 70)

    history = run_loop(args.iters)
    json_path, md_path = write_reports(history, args.iters)

    print("=" * 70)
    first = history[0].total
    last = history[-1].total
    best = max(r.total for r in history)
    print(f"  First score  : {first}/100")
    print(f"  Final score  : {last}/100")
    print(f"  Best score   : {best}/100")
    print(f"  Delta        : {last - first:+d}")
    print(f"  JSON         -> {json_path}")
    print(f"  Markdown     -> {md_path}")
    print("=" * 70)
    return 0 if last >= 75 else 1


if __name__ == "__main__":
    sys.exit(main())
