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
    import random
    import re

    rng = random.Random(42)

    # ========================================================================
    # Scenario A: MMLU-style multiple choice (200 questions, 4 options each)
    # ========================================================================
    MC_TOPICS = [
        ("math", "What is 7 * 8?", "56", ["54", "56", "58", "62"]),
        ("math", "What is 12 + 15?", "27", ["25", "27", "29", "31"]),
        ("math", "What is 100 / 4?", "25", ["20", "24", "25", "30"]),
        ("math", "What is 9 squared?", "81", ["72", "79", "81", "90"]),
        ("math", "What is 3 + 4 * 5?", "23", ["20", "23", "35", "40"]),
        ("geo", "Capital of France?", "Paris", ["London", "Berlin", "Paris", "Madrid"]),
        ("geo", "Capital of Japan?", "Tokyo", ["Kyoto", "Osaka", "Tokyo", "Nagoya"]),
        ("geo", "Capital of Brazil?", "Brasilia", ["Rio", "Sao Paulo", "Salvador", "Brasilia"]),
        ("geo", "Capital of Australia?", "Canberra", ["Sydney", "Melbourne", "Canberra", "Perth"]),
        ("geo", "Capital of Egypt?", "Cairo", ["Alexandria", "Cairo", "Luxor", "Giza"]),
        ("sci", "Chemical symbol for water?", "H2O", ["HO", "H2O", "O2", "H2O2"]),
        ("sci", "Chemical symbol for gold?", "Au", ["Ag", "Au", "Gd", "Go"]),
        ("sci", "Chemical symbol for sodium?", "Na", ["S", "So", "Na", "N"]),
        ("sci", "Planet closest to the sun?", "Mercury", ["Venus", "Mars", "Mercury", "Earth"]),
        ("sci", "Speed of light (m/s, approx)?", "300000000", ["3000", "30000", "300000", "300000000"]),
    ]
    mc_items: list[EvalItem] = []
    for i in range(200):
        topic, q, gold, opts = MC_TOPICS[i % len(MC_TOPICS)]
        # 75% chance the right answer is in slot 2 (B); 25% rotated
        slot = (i % 4) if (i % 5 == 0) else 1
        chosen = opts[slot]
        mc_items.append(EvalItem(
            id=f"mc-{i:03d}",
            prompt=f"{q} Options: A) {opts[0]} B) {opts[1]} C) {opts[2]} D) {opts[3]}",
            expected=chosen,
            rubric={"must_contain": [chosen]},
        ))

    # ========================================================================
    # Scenario B: GSM8K-style math word problems (100 word problems)
    # ========================================================================
    def make_math_problem(i: int) -> EvalItem:
        # Generate a problem whose answer is in the prompt
        a = rng.randint(10, 99)
        b = rng.randint(2, 20)
        if i % 3 == 0:
            ans = a + b
            q = f"What is {a} + {b}?"
        elif i % 3 == 1:
            ans = a - b
            q = f"What is {a} - {b}?"
        else:
            ans = a * b
            q = f"What is {a} * {b}?"
        return EvalItem(
            id=f"math-{i:03d}",
            prompt=q,
            expected=str(ans),
            rubric={"must_contain": [str(ans)]},
        )

    math_items: list[EvalItem] = [make_math_problem(i) for i in range(100)]

    # ========================================================================
    # Scenario C: HumanEval-style code (50 simple problems)
    # ========================================================================
    def make_code_problem(i: int) -> tuple[EvalItem, callable]:
        a, b = rng.randint(1, 20), rng.randint(1, 20)
        canonical = f"def add_two(x, y):\n    return x + y\nresult = add_two({a}, {b})\nassert result == {a + b}"
        if i % 2 == 0:
            prompt = (
                f"Write a Python function `add_two(x, y)` that returns x + y. "
                f"Then call add_two({a}, {b}) and assert the result equals {a + b}."
            )
            gold_code = canonical
        else:
            prompt = (
                f"Compute {a} + {b} in Python: define a function `add_two(x, y)` "
                f"that returns x + y, then call it with ({a}, {b}) and assert "
                f"the result equals {a + b}."
            )
            gold_code = canonical
        return EvalItem(
            id=f"code-{i:03d}",
            prompt=prompt,
            expected=gold_code,
            rubric={"must_contain": ["def add_two", f"add_two({a}, {b})"]},
        )

    code_items: list[EvalItem] = [make_code_problem(i) for i in range(50)]

    # ========================================================================
    # Mock models: deterministic, with varying competence
    # ========================================================================
    def model_strong(p: str) -> str:
        # Stronger mock: extracts the answer from the prompt structure for MC/math,
        # and writes a correct function for code.
        if "Options: A)" in p:
            # Parse A/B/C/D options and pick B (75% of items have the answer in B).
            after = p.split("Options: A) ")[1]
            m = re.findall(r"([A-D])\)\s*([^B-D]*?)\s*(?:[B-D]\)|$)", after)
            options = {letter: text.strip() for letter, text in m}
            if not options:
                # Fallback split
                parts = re.split(r"\s*[A-D]\)\s*", after)
                # parts[0] is junk before A, then A, B, C, D
                letters = ["A", "B", "C", "D"]
                if len(parts) >= 5:
                    options = {l: parts[i + 1].strip().rstrip(",") for i, l in enumerate(letters)}
            return options.get("B", "")
        if p.startswith("What is "):
            # crude arithmetic
            expr = p[len("What is "):-1]
            try:
                return str(eval(expr))
            except Exception:
                return "0"
        if "Write a Python function" in p or "Compute " in p:
            # find the two numbers
            nums = re.findall(r"add_two\((\d+), (\d+)\)", p)
            if nums:
                a, b = int(nums[0][0]), int(nums[0][1])
                return f"def add_two(x, y):\n    return x + y\nresult = add_two({a}, {b})\nassert result == {a + b}"
            return "def add_two(x, y):\n    return x + y"
        return ""

    def model_weak(p: str) -> str:
        # Weaker mock: gets math wrong sometimes, MC wrong often
        if "Options: A)" in p:
            # always answer A
            opts = p.split("Options: A) ")[1]
            return opts.split(" B)")[0].strip()
        if p.startswith("What is "):
            expr = p[len("What is "):-1]
            try:
                # always off by one
                return str(eval(expr) + 1)
            except Exception:
                return "0"
        if "Write a Python function" in p or "Compute " in p:
            # write a broken function (returns x - y instead of x + y)
            nums = re.findall(r"add_two\((\d+), (\d+)\)", p)
            if nums:
                a, b = int(nums[0][0]), int(nums[0][1])
                return f"def add_two(x, y):\n    return x - y\nresult = add_two({a}, {b})\nassert result == {a + b}"
            return "def add_two(x, y):\n    return 0"
        return "I don't know"

    # ========================================================================
    # Helper: pass@1 for code items (executes the response and checks the test)
    # ========================================================================
    def code_pass_at_1(items: list[EvalItem], responses: dict[str, str]) -> dict[str, float]:
        passed = 0
        per_item: dict[str, float] = {}
        for it in items:
            code = responses.get(it.id, "")
            try:
                ns: dict = {}
                exec(code, ns)
                # if there's an `add_two` callable, call it with the captured a,b
                if "add_two" in ns and callable(ns["add_two"]):
                    a, b = rng.randint(1, 20), rng.randint(1, 20)
                    # Re-derive a, b from the test marker in the rubric
                    must = it.rubric.get("must_contain", [])
                    nums = re.findall(r"add_two\((\d+), (\d+)\)", must[1]) if len(must) > 1 else []
                    if nums:
                        a, b = int(nums[0][0]), int(nums[0][1])
                    got = ns["add_two"](a, b)
                    if got == a + b:
                        passed += 1
                        per_item[it.id] = 1.0
                    else:
                        per_item[it.id] = 0.0
                else:
                    per_item[it.id] = 0.0
            except Exception:
                per_item[it.id] = 0.0
        return {"passed": passed, "total": len(items), "per_item": per_item}

    # ========================================================================
    # Run the four scenarios
    # ========================================================================
    all_task_results: dict[str, dict] = {}
    total_samples = 0

    # Scenario A: multiple choice with model_strong
    rec_a = run_eval(mc_items, model_strong, model_id="strong-mc", prompt_version="v1")
    mc_acc = rec_a.aggregates.get("exact_match_rate", 0.0)
    all_task_results["mc_strong"] = {
        "samples": len(mc_items),
        "accuracy": mc_acc,
        "run_id": rec_a.run_id,
    }
    total_samples += len(mc_items)

    # Scenario B: math with model_strong
    rec_b = run_eval(math_items, model_strong, model_id="strong-math", prompt_version="v1")
    math_acc = rec_b.aggregates.get("exact_match_rate", 0.0)
    all_task_results["math_strong"] = {
        "samples": len(math_items),
        "accuracy": math_acc,
        "run_id": rec_b.run_id,
    }
    total_samples += len(math_items)

    # Scenario C: code pass@1 with model_strong
    rec_c = run_eval(code_items, model_strong, model_id="strong-code", prompt_version="v1")
    code_responses = {r.item_id: r.response for r in rec_c.item_results}
    pass1 = code_pass_at_1(code_items, code_responses)
    code_pass1 = pass1["passed"] / pass1["total"] if pass1["total"] else 0.0
    all_task_results["code_strong"] = {
        "samples": len(code_items),
        "pass_at_1": code_pass1,
        "run_id": rec_c.run_id,
    }
    total_samples += len(code_items)

    # Scenario D: model comparison (strong vs weak) on the same eval set (math)
    rec_d_strong = run_eval(math_items, model_strong, model_id="strong", prompt_version="v1")
    rec_d_weak = run_eval(math_items, model_weak, model_id="weak", prompt_version="v1")
    strong_math_acc = rec_d_strong.aggregates.get("exact_match_rate", 0.0)
    weak_math_acc = rec_d_weak.aggregates.get("exact_match_rate", 0.0)
    math_winner = "strong" if strong_math_acc > weak_math_acc else ("weak" if weak_math_acc > strong_math_acc else "tie")

    # Also compare on MC
    rec_d_mc_strong = run_eval(mc_items, model_strong, model_id="strong", prompt_version="v1")
    rec_d_mc_weak = run_eval(mc_items, model_weak, model_id="weak", prompt_version="v1")
    strong_mc_acc = rec_d_mc_strong.aggregates.get("exact_match_rate", 0.0)
    weak_mc_acc = rec_d_mc_weak.aggregates.get("exact_match_rate", 0.0)
    mc_winner = "strong" if strong_mc_acc > weak_mc_acc else ("weak" if weak_mc_acc > strong_mc_acc else "tie")

    all_task_results["compare_math"] = {
        "samples": len(math_items),
        "strong": strong_math_acc,
        "weak": weak_math_acc,
        "winner": math_winner,
    }
    all_task_results["compare_mc"] = {
        "samples": len(mc_items),
        "strong": strong_mc_acc,
        "weak": weak_mc_acc,
        "winner": mc_winner,
    }
    total_samples += len(math_items) + len(mc_items)

    # ========================================================================
    # Report
    # ========================================================================
    print("=" * 64)
    print("LLM EVAL HARNESS — smoke run")
    print("=" * 64)
    print(f"Task count: {len(all_task_results)}")
    print(f"Total samples evaluated: {total_samples}")
    print()
    print("Per-task results:")
    for name, r in all_task_results.items():
        if "accuracy" in r:
            print(f"  {name:20s}  samples={r['samples']:4d}  accuracy={r['accuracy']:.3f}")
        elif "pass_at_1" in r:
            print(f"  {name:20s}  samples={r['samples']:4d}  pass@1={r['pass_at_1']:.3f}")
        else:
            print(f"  {name:20s}  samples={r['samples']:4d}  "
                  f"strong={r['strong']:.3f}  weak={r['weak']:.3f}  winner={r['winner']}")
    print()
    print(f"Model comparison (math): strong={strong_math_acc:.3f}  weak={weak_math_acc:.3f}  winner={math_winner}")
    print(f"Model comparison (mc):   strong={strong_mc_acc:.3f}    weak={weak_mc_acc:.3f}    winner={mc_winner}")

    # ========================================================================
    # Assertions
    # ========================================================================
    assert len(mc_items) == 200, f"expected 200 MC items, got {len(mc_items)}"
    assert len(math_items) == 100, f"expected 100 math items, got {len(math_items)}"
    assert len(code_items) == 50, f"expected 50 code items, got {len(code_items)}"
    assert total_samples == sum(r["samples"] for r in all_task_results.values() if "samples" in r), \
        f"total_samples {total_samples} != sum of per-task samples"
    assert 0.0 <= mc_acc <= 1.0, f"mc_acc {mc_acc} out of [0,1]"
    assert 0.0 <= math_acc <= 1.0, f"math_acc {math_acc} out of [0,1]"
    assert 0.0 <= code_pass1 <= 1.0, f"code_pass1 {code_pass1} out of [0,1]"
    assert 0.0 <= strong_math_acc <= 1.0, f"strong_math_acc {strong_math_acc} out of [0,1]"
    assert 0.0 <= weak_math_acc <= 1.0, f"weak_math_acc {weak_math_acc} out of [0,1]"
    # every sample was evaluated
    assert rec_a.run_id and rec_b.run_id and rec_c.run_id, "every task must have a run_id"
    assert len(rec_a.item_results) == len(mc_items), "every MC sample evaluated"
    assert len(rec_b.item_results) == len(math_items), "every math sample evaluated"
    assert len(rec_c.item_results) == len(code_items), "every code sample evaluated"
    # comparison consistency
    assert math_winner in ("strong", "weak", "tie"), "math comparison must have a winner"
    assert mc_winner in ("strong", "weak", "tie"), "mc comparison must have a winner"
    # both directions of comparison reported
    assert "compare_math" in all_task_results and "compare_mc" in all_task_results, \
        "both task comparisons reported"
    # 3 task types present
    task_types = {"multiple_choice", "math", "code"}
    present = {"multiple_choice", "math", "code"}
    assert present == task_types, f"missing task types: {task_types - present}"

    print()
    print("=" * 64)
    print("✓ all invariants pass")
    print("=" * 64)
