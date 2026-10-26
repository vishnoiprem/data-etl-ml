"""
Pick a rerank threshold on a labeled set.

Given a labeled file of (query, candidate_id, label) and a scoring function,
find the score threshold that maximizes recall at >= target_precision.

Usage:
  python -m service.threshold --labeled data/dev.tsv --target-precision 0.9
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
from statistics import mean
from typing import Iterable

from service.app import fake_cross_encoder_score


def load_labeled(path: Path) -> list[tuple[str, str, int]]:
    """Load (query, candidate_id, candidate_text, label) rows."""
    rows = []
    with path.open() as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.append((r["query"], r["candidate_text"], int(r["label"])))
    return rows


def find_threshold(labeled: list[tuple[str, str, int]], target_precision: float = 0.9) -> dict:
    """Sweep thresholds; pick the smallest one that meets target precision."""
    rows = [(q, t, lab, fake_cross_encoder_score(q, t)) for q, t, lab in labeled]
    rows.sort(key=lambda r: -r[3])

    best = {"threshold": 0.0, "precision": 0.0, "recall": 0.0}
    positives = sum(1 for _, _, lab, _ in rows if lab == 1)
    if positives == 0:
        return best

    above_thr = sum(1 for _, _, lab, _ in rows if lab == 1)
    for i, (_, _, lab, score) in enumerate(rows):
        if i == 0 or rows[i - 1][3] != score:
            kept = rows[: i + 1]
            tp = sum(1 for _, _, l, _ in kept if l == 1)
            fp = sum(1 for _, _, l, _ in kept if l == 0)
            precision = tp / max(1, tp + fp)
            recall = tp / positives
            if precision >= target_precision and recall > best["recall"]:
                best = {"threshold": round(score, 4), "precision": round(precision, 4), "recall": round(recall, 4)}
    return best


def main(labeled_path: str, target_precision: float) -> dict:
    rows = load_labeled(Path(labeled_path))
    result = find_threshold(rows, target_precision)
    print(f"threshold: {result['threshold']}  precision: {result['precision']}  recall: {result['recall']}")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--labeled", required=True)
    p.add_argument("--target-precision", type=float, default=0.9)
    args = p.parse_args()
    main(args.labeled, args.target_precision)
