"""Reproducible LLM evaluation harness: a single run, all metrics, one row.

The shape: load a labeled eval set, call the model on each item,
score with multiple metrics, persist the row. Every run gets a unique
id; a run is reproducible from (run_id, model_id, prompt_version,
eval_set_sha).
"""
from __future__ import annotations
import json
import hashlib
import statistics
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional


@dataclass
class EvalItem:
    id: str
    prompt: str
    expected: str           # gold answer
    rubric: dict = field(default_factory=dict)   # {"must_contain": [...], "must_not_contain": [...]}


@dataclass
class ItemResult:
    item_id: str
    prompt: str
    expected: str
    response: str
    scores: dict            # {"exact_match": 0.0, "rubric_pass": 1.0, "length": 142}


@dataclass
class RunRecord:
    run_id: str
    model_id: str
    prompt_version: str
    eval_set_sha: str
    item_results: list[ItemResult] = field(default_factory=list)
    aggregates: dict = field(default_factory=dict)


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def score_item(item: EvalItem, response: str) -> dict:
    scores: dict = {}
    scores["exact_match"] = 1.0 if response.strip() == item.expected.strip() else 0.0
    must = item.rubric.get("must_contain", [])
    not_ = item.rubric.get("must_not_contain", [])
    if must or not_:
        ok = all(m.lower() in response.lower() for m in must) and all(n.lower() not in response.lower() for n in not_)
        scores["rubric_pass"] = 1.0 if ok else 0.0
    scores["length"] = len(response)
    return scores


def aggregate(results: list[ItemResult]) -> dict:
    keys = set()
    for r in results:
        keys.update(r.scores)
    out: dict = {}
    for k in keys:
        vals = [r.scores[k] for r in results if k in r.scores and isinstance(r.scores[k], (int, float))]
        if vals:
            if all(v in (0.0, 1.0) for v in vals):
                out[f"{k}_rate"] = sum(vals) / len(vals)
            else:
                out[f"{k}_mean"] = statistics.mean(vals)
                out[f"{k}_p95"] = sorted(vals)[int(len(vals) * 0.95)]
    return out


def run_eval(
    items: list[EvalItem],
    model_fn: Callable[[str], str],
    model_id: str,
    prompt_version: str,
) -> RunRecord:
    eval_set_sha = sha("|".join(i.id + i.prompt + i.expected for i in items))
    results: list[ItemResult] = []
    for item in items:
        resp = model_fn(item.prompt)
        scores = score_item(item, resp)
        results.append(ItemResult(item_id=item.id, prompt=item.prompt, expected=item.expected, response=resp, scores=scores))
    run_id = sha(f"{model_id}|{prompt_version}|{eval_set_sha}|{json.dumps([r.scores for r in results], sort_keys=True)}")
    return RunRecord(run_id=run_id, model_id=model_id, prompt_version=prompt_version,
                     eval_set_sha=eval_set_sha, item_results=results, aggregates=aggregate(results))


if __name__ == "__main__":
    items = [
        EvalItem(id="q1", prompt="Capital of France?", expected="Paris",
                 rubric={"must_contain": ["paris"]}),
        EvalItem(id="q2", prompt="Capital of Japan?", expected="Tokyo",
                 rubric={"must_contain": ["tokyo"], "must_not_contain": ["kyoto"]}),
        EvalItem(id="q3", prompt="2+2?", expected="4"),
        EvalItem(id="q4", prompt="Capital of Australia?", expected="Canberra",
                 rubric={"must_contain": ["canberra"], "must_not_contain": ["sydney"]}),
    ]

    # Toy model: just echoes the prompt with the expected answer
    def good_model(p: str) -> str:
        return f"answer: {next((i.expected for i in items if i.prompt == p), '?')}"

    def bad_model(p: str) -> str:
        return "I don't know" if "Capital" in p else "5"

    for model_fn, name in [(good_model, "good"), (bad_model, "bad")]:
        rec = run_eval(items, model_fn, model_id=name, prompt_version="v1")
        print(f"\n=== {name} model ===")
        print(f"run_id:      {rec.run_id}")
        print(f"eval_set:    {rec.eval_set_sha}")
        print(f"aggregates:  {rec.aggregates}")
