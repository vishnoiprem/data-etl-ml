"""
service/eval.py — RAGAS-style metrics + LLM-as-judge for PacificFreight Phase 2.

What this file does
-------------------
- Implements four deterministic metrics that grade a (query, retrieved
  contexts, generated answer, expected) tuple:
    1. Faithfulness        — fraction of answer tokens present in any context
    2. Answer relevance    — Jaccard overlap between question and answer tokens
    3. Context precision   — fraction of retrieved contexts that contain at
                             least one expected-mention token
    4. Context recall      — fraction of expected-mention tokens present in
                             any retrieved context
- Provides a `run_eval(draft_fn, eval_rows, ...)` that runs all rows
  through the service's draft function and produces per-row + aggregate
  results.
- Provides `run_regression_check(aggregate, baseline, threshold)` that
  flags a metric if it dropped by more than `threshold` vs baseline.
- Produces a markdown report.

Mirrors the pattern in `course/hardcode/level-8-evaluation-testing/12-ragas-evaluation.py`
(metrics + regression check) and `11-llm-as-judge-eval.py` (markdown report
shape). Lifted out of those files so this phase's service is self-contained.

How to run as a CLI
-------------------
    python3 eval.py --set ../shared/eval_set.jsonl --report eval_report.md
    python3 eval.py --set ../shared/eval_set.jsonl --baseline baseline.jsonl \\
                   --threshold 0.05 --report eval_report.md

How to import
-------------
    from eval import run_eval, run_regression_check
    rows = [...]                          # the eval set
    results = run_eval(draft_fn, rows)    # returns aggregate + per_row
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Tokenizer (mirrors rag._tokenize but kept local so this file is standalone)
# ---------------------------------------------------------------------------
_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "and", "or", "but", "if", "of", "at", "by", "for", "with", "about",
    "to", "in", "on", "as", "this", "that", "these", "those", "it", "its",
    "i", "you", "we", "they", "he", "she", "my", "your", "our", "their",
    "do", "does", "did", "have", "has", "had", "can", "could", "will",
    "would", "should", "may", "might", "must", "shall", "just", "so",
    "than", "then", "now", "very", "really",
})


def _tokens(text: str) -> set[str]:
    import re
    toks = re.findall(r"\b[a-z0-9_-]+\b", text.lower())
    return {t for t in toks if t not in _STOP_WORDS and len(t) >= 2}


# ---------------------------------------------------------------------------
# Result shapes
# ---------------------------------------------------------------------------
@dataclass
class RowResult:
    id: str
    category: str
    difficulty: str
    expected_shipment_id: str | None
    faithfulness: float
    answer_relevance: float
    context_precision: float
    context_recall: float
    n_contexts: int
    n_expected_mentions: int
    elapsed_ms: int
    error: str | None = None


@dataclass
class Aggregate:
    n_rows: int
    n_errors: int
    faithfulness: float
    answer_relevance: float
    context_precision: float
    context_recall: float
    by_category: dict[str, dict[str, float]] = field(default_factory=dict)
    by_difficulty: dict[str, dict[str, float]] = field(default_factory=dict)
    per_row: list[RowResult] = field(default_factory=list)
    elapsed_total_ms: int = 0


# ---------------------------------------------------------------------------
# The 4 metrics
# ---------------------------------------------------------------------------
def faithfulness(answer: str, contexts: list[str]) -> float:
    """Fraction of answer *content tokens* (length > 2) present in any
    retrieved context. Skips stop words; rounds to 4dp.
    """
    import re
    ans_tokens = [
        t for t in re.findall(r"\b[a-z0-9_-]+\b", answer.lower())
        if t not in _STOP_WORDS and len(t) > 2
    ]
    if not ans_tokens:
        return 1.0
    ctx_text = " ".join(contexts).lower()
    supported = sum(1 for t in ans_tokens if t in ctx_text)
    return round(supported / len(ans_tokens), 4)


def answer_relevance(question: str, answer: str) -> float:
    """Jaccard overlap between question tokens and answer tokens."""
    q = _tokens(question)
    a = _tokens(answer)
    if not q or not a:
        return 0.0
    return round(len(q & a) / len(q | a), 4)


def context_precision(contexts: list[str], expected_mentions: list[str]) -> float:
    """Fraction of retrieved contexts that contain at least one
    expected-mention token. A precision of 0 means retrieval missed
    everything; 1 means every retrieved context is on-target.
    """
    if not contexts:
        return 0.0
    expected = [m.lower() for m in (expected_mentions or [])]
    if not expected:
        return 0.0
    hits = 0
    for c in contexts:
        c_low = c.lower()
        if any(m in c_low for m in expected):
            hits += 1
    return round(hits / len(contexts), 4)


def context_recall(contexts: list[str], expected_mentions: list[str]) -> float:
    """Fraction of expected-mention tokens present in any retrieved context."""
    expected = [m.lower() for m in (expected_mentions or [])]
    if not expected:
        return 0.0
    ctx_text = " ".join(contexts).lower()
    found = sum(1 for m in expected if m in ctx_text)
    return round(found / len(expected), 4)


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------
def run_eval(
    draft_fn,
    rows: list[dict],
    *,
    verbose: bool = False,
) -> Aggregate:
    """Run every row through `draft_fn(row)` and compute the 4 metrics.

    `draft_fn` is the service's draft function. It takes an eval row and
    returns a dict with at least:
        {
            "draft": str,
            "contexts": list[str],   # retrieved chunks used in the prompt
        }
    Any exception is captured into the row's `error` field; the run
    continues so one bad row doesn't kill the whole eval.
    """
    per_row: list[RowResult] = []
    started = time.monotonic()

    for row in rows:
        row_started = time.monotonic()
        try:
            out = draft_fn(row)
            draft = out.get("draft", "") or ""
            contexts = out.get("contexts", []) or []
            err = None
        except Exception as exc:  # noqa: BLE001
            draft = ""
            contexts = []
            err = f"{type(exc).__name__}: {exc}"
        elapsed_ms = int((time.monotonic() - row_started) * 1000)

        result = RowResult(
            id=row.get("id", "?"),
            category=row.get("category", "?"),
            difficulty=row.get("difficulty", "?"),
            expected_shipment_id=row.get("expected_shipment_id"),
            faithfulness=faithfulness(draft, contexts),
            answer_relevance=answer_relevance(row.get("email", ""), draft),
            context_precision=context_precision(contexts, row.get("expected_mentions", [])),
            context_recall=context_recall(contexts, row.get("expected_mentions", [])),
            n_contexts=len(contexts),
            n_expected_mentions=len(row.get("expected_mentions", []) or []),
            elapsed_ms=elapsed_ms,
            error=err,
        )
        per_row.append(result)
        if verbose:
            print(
                f"  {result.id:10s} cat={result.category:6s} "
                f"faith={result.faithfulness:.2f} "
                f"ansrel={result.answer_relevance:.2f} "
                f"ctxp={result.context_precision:.2f} "
                f"ctxr={result.context_recall:.2f} "
                f"err={result.error}"
            )

    n_errors = sum(1 for r in per_row if r.error)
    agg = _aggregate(per_row, n_errors, started)
    return agg


def _aggregate(per_row: list[RowResult], n_errors: int, started: float) -> Aggregate:
    def _mean(xs: list[float]) -> float:
        return round(statistics.mean(xs), 4) if xs else 0.0

    by_cat: dict[str, list[RowResult]] = {}
    by_diff: dict[str, list[RowResult]] = {}
    for r in per_row:
        by_cat.setdefault(r.category, []).append(r)
        by_diff.setdefault(r.difficulty, []).append(r)

    def _agg_dict(rs: list[RowResult]) -> dict[str, float]:
        return {
            "n": len(rs),
            "faithfulness": _mean([r.faithfulness for r in rs]),
            "answer_relevance": _mean([r.answer_relevance for r in rs]),
            "context_precision": _mean([r.context_precision for r in rs]),
            "context_recall": _mean([r.context_recall for r in rs]),
        }

    return Aggregate(
        n_rows=len(per_row),
        n_errors=n_errors,
        faithfulness=_mean([r.faithfulness for r in per_row]),
        answer_relevance=_mean([r.answer_relevance for r in per_row]),
        context_precision=_mean([r.context_precision for r in per_row]),
        context_recall=_mean([r.context_recall for r in per_row]),
        by_category={k: _agg_dict(v) for k, v in sorted(by_cat.items())},
        by_difficulty={k: _agg_dict(v) for k, v in sorted(by_diff.items())},
        per_row=per_row,
        elapsed_total_ms=int((time.monotonic() - started) * 1000),
    )


# ---------------------------------------------------------------------------
# Regression check + baseline I/O
# ---------------------------------------------------------------------------
@dataclass
class Regression:
    metric: str
    current: float
    baseline: float
    delta: float
    threshold: float
    regressed: bool


def run_regression_check(
    aggregate: Aggregate,
    baseline: Aggregate | None,
    threshold: float,
) -> list[Regression]:
    """Flag any metric whose current value dropped by more than
    `threshold` (in absolute terms) versus the baseline. Returns the
    full list (regressed and not) so the report can show both.

    `threshold=0.05` means: trip if `current - baseline <= -0.05`.
    """
    if baseline is None:
        return []
    metrics = ["faithfulness", "answer_relevance", "context_precision", "context_recall"]
    out: list[Regression] = []
    for m in metrics:
        cur = getattr(aggregate, m)
        base = getattr(baseline, m)
        delta = round(cur - base, 4)
        out.append(Regression(
            metric=m,
            current=cur,
            baseline=base,
            delta=delta,
            threshold=threshold,
            regressed=delta <= -threshold,
        ))
    return out


def save_baseline(aggregate: Aggregate, path: Path) -> None:
    """Write the aggregate as jsonl, one metric per line."""
    with path.open("w") as fh:
        for m in ["faithfulness", "answer_relevance", "context_precision", "context_recall"]:
            fh.write(json.dumps({"metric": m, "value": getattr(aggregate, m)}) + "\n")


def load_baseline(path: Path) -> dict[str, float] | None:
    """Read a baseline.jsonl back as {metric: value}."""
    if not path.exists():
        return None
    out: dict[str, float] = {}
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out[d["metric"]] = d["value"]
    return out


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------
def render_report(
    aggregate: Aggregate,
    regressions: list[Regression] | None = None,
    threshold: float = 0.05,
) -> str:
    """Render the aggregate + regression check as a markdown report."""
    lines: list[str] = []
    lines.append("# Phase 2 — Eval Report")
    lines.append("")
    lines.append(f"Rows: **{aggregate.n_rows}**  |  Errors: **{aggregate.n_errors}**  |  Total time: **{aggregate.elapsed_total_ms} ms**")
    lines.append("")
    lines.append("## Aggregate metrics")
    lines.append("")
    lines.append("| Metric | Score |")
    lines.append("|---|---|")
    for m in ["faithfulness", "answer_relevance", "context_precision", "context_recall"]:
        lines.append(f"| {m} | {getattr(aggregate, m):.4f} |")
    lines.append("")

    lines.append("## By category")
    lines.append("")
    lines.append("| Category | n | faith | ansrel | ctxp | ctxr |")
    lines.append("|---|---|---|---|---|---|")
    for cat, m in aggregate.by_category.items():
        lines.append(
            f"| {cat} | {m['n']} | {m['faithfulness']:.3f} | "
            f"{m['answer_relevance']:.3f} | {m['context_precision']:.3f} | "
            f"{m['context_recall']:.3f} |"
        )
    lines.append("")

    lines.append("## By difficulty")
    lines.append("")
    lines.append("| Difficulty | n | faith | ansrel | ctxp | ctxr |")
    lines.append("|---|---|---|---|---|---|")
    for diff, m in aggregate.by_difficulty.items():
        lines.append(
            f"| {diff} | {m['n']} | {m['faithfulness']:.3f} | "
            f"{m['answer_relevance']:.3f} | {m['context_precision']:.3f} | "
            f"{m['context_recall']:.3f} |"
        )
    lines.append("")

    if regressions is not None:
        lines.append("## Regression check (threshold = " + str(threshold) + ")")
        lines.append("")
        if not regressions:
            lines.append("_No baseline supplied; skipping regression check._")
        else:
            lines.append("| Metric | Current | Baseline | Delta | Status |")
            lines.append("|---|---|---|---|---|")
            for r in regressions:
                status = "🔴 REGRESSED" if r.regressed else "✓ ok"
                lines.append(
                    f"| {r.metric} | {r.current:.4f} | {r.baseline:.4f} | "
                    f"{r.delta:+.4f} | {status} |"
                )
        lines.append("")

    lines.append("## Per-row detail")
    lines.append("")
    lines.append("| ID | cat | diff | faith | ansrel | ctxp | ctxr | contexts | mentions | err |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in aggregate.per_row:
        err = r.error or ""
        lines.append(
            f"| {r.id} | {r.category} | {r.difficulty} | {r.faithfulness:.2f} | "
            f"{r.answer_relevance:.2f} | {r.context_precision:.2f} | "
            f"{r.context_recall:.2f} | {r.n_contexts} | {r.n_expected_mentions} | {err} |"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Phase 3: Iteration report (joins eval + feedback + cost)
# ---------------------------------------------------------------------------
def render_iteration_report(
    *,
    usage_log_path: Path,
    since_seconds: float = 7 * 24 * 3600,  # default 7 days
    baseline_path: Path | None = None,
    eval_set_path: Path | None = None,
) -> str:
    """Render an iteration report joining:
       - online metrics (drafts, errors, latency from usage.jsonl)
       - feedback (thumbs up/down from /feedback)
       - cost (sum of cost_usd)
       - eval (optional re-run of the eval set vs baseline)

    This is the artifact the FDE reviews every Monday in the iteration
    cadence. Designed to fit in one screen: top-line health, then
    feedback breakdown, then per-day totals.
    """
    now = time.time()
    cutoff = now - since_seconds
    events: list[dict] = []
    if usage_log_path.exists():
        with usage_log_path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("ts", 0) >= cutoff:
                    events.append(e)

    # Partition events
    drafts = [e for e in events if e.get("outcome") in ("ok", "fallback", "error")]
    feedbacks = [e for e in events if e.get("outcome") == "feedback"]
    fallbacks = [e for e in events if e.get("outcome") == "fallback"]
    rate_limited = [e for e in events if e.get("outcome") == "rate_limited"]

    # Feedback breakdown
    thumbs_up = sum(1 for e in feedbacks if e.get("feedback_rating") == 1)
    thumbs_down = sum(1 for e in feedbacks if e.get("feedback_rating") == -1)
    thumbs_neutral = sum(1 for e in feedbacks if e.get("feedback_rating") == 0)
    total_thumbs = thumbs_up + thumbs_down + thumbs_neutral
    thumbs_up_rate = (thumbs_up / total_thumbs * 100.0) if total_thumbs else 0.0

    # Cost + latency
    total_cost = sum(e.get("cost_usd", 0.0) for e in drafts)
    latencies = [e.get("latency_ms", 0) for e in drafts if e.get("latency_ms", 0) > 0]
    p50 = statistics.median(latencies) if latencies else 0.0
    p95 = sorted(latencies)[int(0.95 * len(latencies))] if latencies else 0.0

    # Per-day
    per_day: dict[str, dict[str, float]] = {}
    for e in drafts:
        day = time.strftime("%Y-%m-%d", time.localtime(e.get("ts", 0)))
        d = per_day.setdefault(day, {"n": 0, "cost": 0.0, "errors": 0})
        d["n"] += 1
        d["cost"] += e.get("cost_usd", 0.0)
        if e.get("outcome") != "ok":
            d["errors"] += 1

    # Build the markdown
    L: list[str] = []
    L.append("# Iteration Report (Phase 3 T2)")
    L.append("")
    L.append(f"Window: last {int(since_seconds / 86400)} days  |  Cutoff: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cutoff))}")
    L.append("")

    # Top-line health
    L.append("## Top-line")
    L.append("")
    L.append(f"| Metric | Value |")
    L.append(f"|---|---|")
    L.append(f"| Drafts | {len(drafts)} |")
    L.append(f"| Fallback responses | {len(fallbacks)} |")
    L.append(f"| Rate-limited | {len(rate_limited)} |")
    L.append(f"| Total cost | ${total_cost:.4f} |")
    L.append(f"| P50 latency | {p50:.0f} ms |")
    L.append(f"| P95 latency | {p95:.0f} ms |")
    L.append("")

    # Feedback
    L.append("## Feedback (CS team thumbs)")
    L.append("")
    if total_thumbs == 0:
        L.append("_No feedback recorded yet — the CS team hasn't used /feedback._")
    else:
        L.append(f"| Rating | Count | % |")
        L.append(f"|---|---|---|")
        L.append(f"| 👍 (+1) | {thumbs_up} | {thumbs_up/total_thumbs*100:.1f}% |")
        L.append(f"| 👎 (-1) | {thumbs_down} | {thumbs_down/total_thumbs*100:.1f}% |")
        L.append(f"| 😐 (0) | {thumbs_neutral} | {thumbs_neutral/total_thumbs*100:.1f}% |")
        L.append("")
        L.append(f"**Thumbs-up rate: {thumbs_up_rate:.1f}%**  (target: ≥ 80% for Phase 3 sign-off)")
    L.append("")

    # Per-day breakdown
    L.append("## Per-day breakdown")
    L.append("")
    L.append("| Day | Drafts | Cost (USD) | Errors |")
    L.append("|---|---|---|---|")
    for day in sorted(per_day.keys()):
        d = per_day[day]
        L.append(f"| {day} | {int(d['n'])} | ${d['cost']:.4f} | {int(d['errors'])} |")
    L.append("")

    # Top notes (thumbs-down free text)
    bad_notes = [e.get("note", "") for e in feedbacks
                 if e.get("feedback_rating") == -1 and e.get("note")]
    if bad_notes:
        L.append("## Recent thumbs-down notes")
        L.append("")
        for note in bad_notes[:5]:
            L.append(f"- {note}")
        L.append("")

    # Optional: eval delta vs baseline
    if eval_set_path and eval_set_path.exists() and baseline_path and baseline_path.exists():
        L.append("## Eval delta vs baseline")
        L.append("")
        try:
            rows = _load_eval_set(eval_set_path)
            agg = run_eval(_default_draft_fn, rows, verbose=False)
            bd = load_baseline(baseline_path)
            if bd:
                L.append("| Metric | Current | Baseline | Delta |")
                L.append("|---|---|---|---|")
                for m in ("faithfulness", "answer_relevance", "context_precision", "context_recall"):
                    cur = getattr(agg, m)
                    base = bd.get(m, 0.0)
                    delta = cur - base
                    flag = "🔴" if delta < -0.05 else ("🟢" if delta > 0.02 else "🟡")
                    L.append(f"| {m} | {cur:.4f} | {base:.4f} | {delta:+.4f} {flag} |")
        except Exception as e:
            L.append(f"_Eval run skipped: {e}_")
        L.append("")

    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _load_eval_set(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _default_draft_fn(row: dict) -> dict:
    """Standalone draft fn for the CLI: imports the service app's
    `draft` function via a small indirection so this file stays
    importable without a running service.

    For the CLI we re-implement the bare-minimum pipeline: regex-extract
    the shipment ID, look it up, build a minimal RAG prompt, and call
    the Phase 1 mock LLM. The real service (`app.py`) does the same
    thing but goes through FastAPI.
    """
    import re
    import importlib.util
    from pathlib import Path as _P

    # 1. Extract shipment ID from the email (regex, then take the last).
    text = row.get("email", "")
    m = re.search(r"PF-\s*\d{4,5}", text)
    shipment_id = m.group(0).replace(" ", "").upper() if m else None

    # 2. Look it up in the tracker.
    tracker = _P(__file__).parent.parent.parent / "phase-1-foundations" / "shared" / "shipments.json"
    shipment = None
    contexts: list[str] = []
    if shipment_id and tracker.exists():
        with tracker.open() as fh:
            data = json.load(fh)
        for s in data["shipments"]:
            if s["id"] == shipment_id:
                shipment = s
                contexts.append(
                    f"Shipment {s['id']} status={s.get('status')} "
                    f"customer={s.get('customer_name')} "
                    f"last_event={s.get('last_event')}"
                )
                break

    # 3. Build a minimal RAG prompt and call Phase 1's complete().
    system = (
        "You are PacificFreight's customer-service drafter. "
        "Follow the style guide. Reply in the customer's language. "
        "Output ONLY the reply."
    )
    if shipment is not None:
        system += f"\n\nShipment context:\n{json.dumps(shipment, ensure_ascii=False)}"
    if contexts:
        system += "\n\nRetrieved context:\n" + "\n".join(contexts)

    spec = importlib.util.spec_from_file_location(
        "pf_llm",
        _P(__file__).parent.parent.parent / "phase-1-foundations" / "technical" / "03-modern-ai-tooling.py",
    )
    pf_llm = importlib.util.module_from_spec(spec)
    sys.modules["pf_llm"] = pf_llm  # required so @dataclass in the module can resolve
    spec.loader.exec_module(pf_llm)

    out = pf_llm.complete(system=system, user=text)
    return {"draft": out.text, "contexts": contexts}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=False)

    # Default: run the eval
    p_eval = sub.add_parser("eval", help="Run the eval set and render a report (default)")
    p_eval.add_argument("--set", type=Path, required=True, help="Path to eval_set.jsonl")
    p_eval.add_argument("--report", type=Path, default=Path("eval_report.md"))
    p_eval.add_argument("--baseline", type=Path, default=None, help="baseline.jsonl to compare against")
    p_eval.add_argument("--threshold", type=float, default=0.05, help="regression threshold (default 0.05)")
    p_eval.add_argument("--save-baseline", type=Path, default=None, help="if set, write current aggregate as baseline.jsonl")
    p_eval.add_argument("--verbose", action="store_true")

    # Phase 3: iteration report
    p_iter = sub.add_parser("iteration-report", help="Render the weekly iteration report (Phase 3 T2)")
    p_iter.add_argument("--usage-log", type=Path, default=Path("usage.jsonl"),
                        help="Path to usage.jsonl (default: usage.jsonl)")
    p_iter.add_argument("--since-days", type=float, default=7.0,
                        help="Window in days (default 7)")
    p_iter.add_argument("--report", type=Path, default=Path("iteration_report.md"),
                        help="Output path (default: iteration_report.md)")
    p_iter.add_argument("--baseline", type=Path, default=None,
                        help="Optional baseline.jsonl to include an eval delta")
    p_iter.add_argument("--eval-set", type=Path, default=None,
                        help="Optional eval_set.jsonl to include an eval delta")

    args = parser.parse_args()
    if args.cmd is None or args.cmd == "eval":
        return _run_eval_cmd(args)
    if args.cmd == "iteration-report":
        md = render_iteration_report(
            usage_log_path=args.usage_log,
            since_seconds=args.since_days * 86400.0,
            baseline_path=args.baseline,
            eval_set_path=args.eval_set,
        )
        args.report.write_text(md, encoding="utf-8")
        print(f"Wrote iteration report to {args.report}", file=sys.stderr)
        return 0
    parser.print_help()
    return 1


def _run_eval_cmd(args) -> int:
    if not args.set.exists():
        print(f"ERROR: eval set not found at {args.set}", file=sys.stderr)
        return 1

    rows = _load_eval_set(args.set)
    print(f"Running eval on {len(rows)} rows from {args.set} ...", file=sys.stderr)
    aggregate = run_eval(_default_draft_fn, rows, verbose=args.verbose)
    print(f"  faithfulness={aggregate.faithfulness:.3f}  ansrel={aggregate.answer_relevance:.3f}  "
          f"ctxp={aggregate.context_precision:.3f}  ctxr={aggregate.context_recall:.3f}  "
          f"errors={aggregate.n_errors}", file=sys.stderr)

    baseline_dict = load_baseline(args.baseline) if args.baseline else None
    baseline_agg: Aggregate | None = None
    if baseline_dict:
        baseline_agg = Aggregate(
            n_rows=0, n_errors=0,
            faithfulness=baseline_dict.get("faithfulness", 0.0),
            answer_relevance=baseline_dict.get("answer_relevance", 0.0),
            context_precision=baseline_dict.get("context_precision", 0.0),
            context_recall=baseline_dict.get("context_recall", 0.0),
        )
    regressions = run_regression_check(aggregate, baseline_agg, args.threshold)

    md = render_report(aggregate, regressions, args.threshold)
    args.report.write_text(md, encoding="utf-8")
    print(f"Wrote report to {args.report}", file=sys.stderr)

    if args.save_baseline:
        save_baseline(aggregate, args.save_baseline)
        print(f"Saved baseline to {args.save_baseline}", file=sys.stderr)

    if any(r.regressed for r in regressions):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
