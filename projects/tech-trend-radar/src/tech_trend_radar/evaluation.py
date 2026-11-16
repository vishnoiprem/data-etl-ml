"""The evaluation harness.

`make eval` measures how well the radar does at the one thing that matters:
putting the topics that are actually accelerating at the top.

**Burst detection accuracy.** The harness builds a synthetic corpus where the
ground truth is known by construction — a set of topics that are accelerating
and a set that are steady — and checks whether the accelerating ones come
out on top. This is the only honest way to measure burst detection without
hand-labelling a live corpus, and it tests the detector rather than the
vocabulary.

**Ranking metrics.** `precision@k`, `recall@k`, `MRR` and `NDCG@k` over the
live snapshot, measured against a gold set of topics that the corpus
genuinely contains.

**Source coverage.** How many platforms contributed, and whether any failed.
A radar that silently loses half its sources is worse than one that says so.

The acceptance thresholds are stated explicitly in `ACCEPTANCE`, and
`check_acceptance` turns them into a pass or a fail.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .burst import burst_report
from .collector import load_latest_snapshot
from .config import Settings, load_settings
from .models import Post
from .ranking import build_trends
from .semantic import SemanticMatcher, build_matcher

#: The acceptance thresholds. `make eval` exits non-zero if any of these
#: is missed, so the eval is a gate rather than a report.
ACCEPTANCE: dict[str, float] = {
    #: The accelerating topics must outrank the steady ones.
    "min_burst_accuracy": 0.9,
    #: At least this many sources must contribute.
    "min_live_sources": 4.0,
    #: A snapshot must contain at least this many posts to be worth ranking.
    "min_post_count": 100.0,
}


@dataclass(slots=True)
class EvalResult:
    """The outcome of one evaluation run."""

    name: str
    passed: bool
    metrics: dict = field(default_factory=dict)
    detail: str = ""
    #: True when the evaluation could not run at all — a missing input
    #: rather than a failure. A skipped evaluation does not fail the gate.
    skipped: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "metrics": self.metrics,
            "detail": self.detail,
            "skipped": self.skipped,
        }


# ----------------------------------------------------------------------
# Ranking metrics
# ----------------------------------------------------------------------


def precision_at_k(ranked: list[str], gold: set[str], k: int) -> float:
    """How many of the top k are in the gold set."""
    if k <= 0:
        return 0.0
    hits = sum(1 for topic in ranked[:k] if topic in gold)
    return hits / k


def recall_at_k(ranked: list[str], gold: set[str], k: int) -> float:
    """How much of the gold set is in the top k."""
    if not gold:
        return 0.0
    hits = sum(1 for topic in ranked[:k] if topic in gold)
    return hits / len(gold)


def mrr(ranked: list[str], gold: set[str]) -> float:
    """The reciprocal of the rank of the first correct answer."""
    for index, topic in enumerate(ranked, start=1):
        if topic in gold:
            return 1.0 / index
    return 0.0


def ndcg_at_k(ranked: list[str], gold: set[str], k: int) -> float:
    """Normalised discounted cumulative gain at k.

    A hit at position 1 counts more than a hit at position 10, and the
    score is normalised by the best possible ordering.
    """
    if not gold:
        return 0.0
    dcg = sum(
        1.0 / math.log2(index + 1)
        for index, topic in enumerate(ranked[:k], start=1)
        if topic in gold
    )
    ideal_hits = min(len(gold), k)
    idcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0


# ----------------------------------------------------------------------
# The synthetic burst fixture
# ----------------------------------------------------------------------


def build_burst_fixture(
    now: datetime,
    accelerating: tuple[str, ...] = ("rust", "kubernetes", "postgres", "wasm"),
    steady: tuple[str, ...] = ("python", "docker", "react", "linux"),
) -> tuple[list[Post], set[str]]:
    """A corpus where the ground truth is known by construction.

    Each *accelerating* topic gets a burst of mentions in the recent window
    and almost none in the baseline. Each *steady* topic gets a flat rate
    across both windows. A detector that cannot tell those apart is not
    detecting bursts, it is counting.

    The fixture is built from synthetic posts with real platform names, so
    the cross-platform corroboration path is exercised too.
    """
    posts: list[Post] = []
    platforms = ("hackernews", "devto", "stackoverflow")

    for topic in accelerating:
        # 9 recent mentions, 1 in the baseline.
        for n in range(9):
            posts.append(
                _post(f"acc-{topic}-{n}", topic, now - timedelta(hours=2 + n), platforms[n % 3])
            )
        posts.append(_post(f"acc-{topic}-old", topic, now - timedelta(days=5), platforms[0]))

    for topic in steady:
        # A flat rate across both windows. The recent window is 72 hours
        # and the baseline is 168, so the two windows hold different
        # amounts of time — the steady topic is spread evenly *by rate*,
        # not by count, which is what "not accelerating" means.
        for n in range(6):
            posts.append(
                _post(f"steady-{topic}-{n}", topic, now - timedelta(hours=12 * n + 2), platforms[n % 3])
            )
            posts.append(
                _post(f"steady-{topic}-old-{n}", topic, now - timedelta(hours=72 + 12 * n + 2), platforms[n % 3])
            )

    return posts, set(accelerating)


def _post(
    native_id: str,
    topic: str,
    published: datetime,
    platform: str,
) -> Post:
    """One synthetic post, titled so the topic is the only thing in it."""
    return Post(
        platform=platform,
        native_id=native_id,
        title=f"Everything about {topic} you need to know",
        published=published,
        weight=1.0,
        raw_engagement=100,
        url=f"https://example.invalid/{native_id}",
        tags=(platform,),
    )


# ----------------------------------------------------------------------
# The evaluation runs
# ----------------------------------------------------------------------


def eval_burst_detection(settings: Settings, semantic: SemanticMatcher | None = None) -> EvalResult:
    """Does the detector put the accelerating topics on top?"""
    now = datetime.now(timezone.utc)
    posts, gold = build_burst_fixture(now)

    ranked = [
        signal.topic
        for signal, _ in burst_report(posts, settings, now=now, limit=20, semantic=semantic)
    ]
    top = len(gold)
    hits = sum(1 for topic in ranked[:top] if topic in gold)

    accuracy = hits / top if top else 0.0
    metrics = {
        "accuracy": round(accuracy, 4),
        "gold_size": float(len(gold)),
        "hits_at_top": float(hits),
        "ranked": ranked[:12],
    }
    passed = accuracy >= ACCEPTANCE["min_burst_accuracy"]
    detail = (
        f"{hits}/{top} accelerating topics in the top {top} "
        f"(threshold {ACCEPTANCE['min_burst_accuracy']})"
    )
    return EvalResult("burst_detection", passed, metrics, detail)


def eval_ranking(snapshot, settings: Settings, semantic: SemanticMatcher | None = None) -> EvalResult:
    """Ranking metrics over the live snapshot.

    The gold set is the topics the corpus genuinely contains, discovered by
    looking at which topics clear the mention threshold at all. This
    measures whether the *ordering* is right given what is in the corpus,
    which is the part the ranking controls.
    """
    if snapshot is None or not snapshot.posts:
        return EvalResult(
            "ranking",
            True,
            {},
            "no snapshot available — run `make fetch` to measure ranking",
            skipped=True,
        )

    posts = snapshot.posts
    trends = build_trends(posts, settings, limit=50, semantic=semantic)
    ranked = [t.topic for t in trends]

    # The gold set: every topic that clears the mention bar somewhere in
    # the corpus, which is a superset of what trends.
    from .burst import detect_bursts

    signals = detect_bursts(posts, settings, semantic=semantic)
    gold = {topic for topic, signal in signals.items() if signal.recent_mentions >= 3}

    k = 10
    metrics = {
        "precision_at_10": round(precision_at_k(ranked, gold, k), 4),
        "recall_at_10": round(recall_at_k(ranked, gold, k), 4),
        "mrr": round(mrr(ranked, gold), 4),
        "ndcg_at_10": round(ndcg_at_k(ranked, gold, k), 4),
        "ranked_topics": float(len(ranked)),
        "gold_topics": float(len(gold)),
    }
    # The ranking is measured, not gated: what is "good" here depends
    # entirely on what the corpus happens to contain, and a hard threshold
    # would just be a threshold on the live data's shape.
    return EvalResult(
        "ranking",
        True,
        metrics,
        f"{len(ranked)} topics ranked, {len(gold)} in the gold set",
    )


def eval_coverage(snapshot, settings: Settings) -> EvalResult:
    """Did enough sources contribute?"""
    if snapshot is None:
        # No snapshot is a missing input, not a coverage failure. A radar
        # that collected nothing has not been *tested* — it has not been
        # run. Failing the gate here would make `make eval` unusable
        # before the first `make fetch`, which is exactly when it is most
        # useful to run it.
        return EvalResult(
            "coverage",
            True,
            {},
            "no snapshot available — run `make fetch` to measure coverage",
            skipped=True,
        )

    live = len(snapshot.ok_platforms)
    failed = len(snapshot.failed_platforms)
    metrics = {
        "live_sources": float(live),
        "failed_sources": float(failed),
        "post_count": float(len(snapshot.posts)),
    }

    passed = (
        live >= ACCEPTANCE["min_live_sources"]
        and len(snapshot.posts) >= ACCEPTANCE["min_post_count"]
    )
    detail = (
        f"{live} live sources (need {int(ACCEPTANCE['min_live_sources'])}), "
        f"{len(snapshot.posts)} posts (need {int(ACCEPTANCE['min_post_count'])})"
    )
    return EvalResult("coverage", passed, metrics, detail)


def run_eval(settings: Settings | None = None) -> list[EvalResult]:
    """Every evaluation, in order."""
    settings = settings or load_settings()
    snapshot = load_latest_snapshot(settings)
    # The evaluation must measure the pipeline that actually runs, so it
    # builds the same matcher the service does. When the embedding model
    # is unavailable, this is None and the evaluation measures the lexical
    # pipeline — which is exactly what is running.
    semantic = build_matcher(settings)
    return [
        eval_burst_detection(settings, semantic=semantic),
        eval_ranking(snapshot, settings, semantic=semantic),
        eval_coverage(snapshot, settings),
    ]


def check_acceptance(results: list[EvalResult]) -> bool:
    """Whether every gated evaluation passed.

    A skipped evaluation does not fail the gate — it never ran, so it
    cannot have failed. The ranking evaluation is never gated at all:
    what counts as "good" depends on what the live corpus contains, and
    a threshold there would only measure the shape of the live data.
    """
    return all(r.passed for r in results if r.name != "ranking" and not r.skipped)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Tech Trend Radar evaluation.")
    parser.add_argument("--out", default="", help="Write the results to this JSON file.")
    args = parser.parse_args(argv)

    settings = load_settings()
    results = run_eval(settings)

    print("Tech Trend Radar — evaluation")
    print("=" * 72)
    for result in results:
        if result.skipped:
            status = "SKIP"
        elif result.passed:
            status = "PASS"
        else:
            status = "FAIL"
        print(f"\n[{status}] {result.name}: {result.detail}")
        for key, value in result.metrics.items():
            if isinstance(value, list):
                print(f"    {key}: {', '.join(str(v) for v in value[:8])}")
            else:
                print(f"    {key}: {value}")

    passed = check_acceptance(results)
    print("\n" + "=" * 72)
    print(f"Acceptance: {'PASS' if passed else 'FAIL'}")

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "acceptance": {k: v for k, v in ACCEPTANCE.items()},
                    "passed": passed,
                    "results": [r.to_dict() for r in results],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"Wrote {path}")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
