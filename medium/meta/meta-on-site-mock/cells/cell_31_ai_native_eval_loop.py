"""
Cell 31: AI-Native Eval-Driven Deployment Loop

The interview question:
'You ship LLM-powered features to 1B users. How do you make sure
 a prompt change doesn't break the product? How do you decide
 when to roll back? When is LLM-as-judge trustworthy enough to
 ship without human review?'

L6 answer structure:
- AI-native = eval is in the deploy loop, not after
- 4 layers: prompt versioning, eval set in CI, canary on shadow, auto-rollback
- LLM-as-judge has a calibration problem (inter-rater agreement <1.0)
- The cardinal sin: ship a prompt change without measuring
"""
import random
import json
import sqlite3
import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ════════════════════════════════════════════════════════════════
# THE 4 LAYERS OF AI-NATIVE DEPLOYMENT
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("THE 4 LAYERS (the AI-native deployment loop)")
print("=" * 70)
print("""
LAYER 1: PROMPT VERSIONING
   Every prompt has a version. Every trace records which version.
   prompts(prompt_id, version, template, model, created_at)
   traces(prompt_version REFERENCES prompts(version))

LAYER 2: EVAL SET IN CI
   PR opens -> CI runs eval set against new prompt
   - 1000 labeled (query, expected_answer) pairs
   - 200 ground-truth retrieval pairs
   - 50 LLM-as-judge calibration examples
   - Block merge if Recall@8 < 0.85 OR judge score < 4.0/5
   - Eval set versioned like code (never overwrite, only add)

LAYER 3: CANARY ON SHADOW
   New prompt serves 1% of traffic in parallel
   Compare 5 metrics vs old prompt: Recall@8, judge, p95, cost, satisfaction
   Auto-promote if all green for 24h
   Auto-rollback if any metric regresses > 5pp

LAYER 4: AUTO-ROLLBACK
   Watch the dashboard for 7 days post-promotion
   If satisfaction drops > 3pp OR p95 > 1s OR hallucination > 0.1%
     -> automatic rollback to previous prompt version
   Rollback is a config push, not a re-deploy
   Time-to-rollback: < 5 minutes
""")

# ════════════════════════════════════════════════════════════════
# SIMULATION: the eval-driven deploy loop
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("SIMULATION: PR opens, eval runs, decide ship")
print("=" * 70)

# Build the eval set
conn = sqlite3.connect(':memory:')
conn.executescript("""
    CREATE TABLE prompts (
        prompt_id TEXT PRIMARY KEY,
        version INT,
        template TEXT,
        model TEXT,
        created_at TIMESTAMP
    );

    CREATE TABLE eval_set (
        eval_id TEXT PRIMARY KEY,
        query TEXT,
        expected_chunks TEXT,    -- ground truth retrieval
        expected_answer TEXT,    -- ground truth generation
        difficulty TEXT          -- 'easy' | 'medium' | 'hard'
    );

    CREATE TABLE eval_run (
        run_id TEXT PRIMARY KEY,
        prompt_version INT,
        pr_number INT,
        timestamp TIMESTAMP,
        recall_at_8 REAL,
        judge_score REAL,
        hallucination_rate REAL,
        cost_per_query REAL,
        verdict TEXT    -- 'ship' | 'block' | 'manual_review'
    );
""")

# Seed: 3 prompt versions, 200 eval queries, 3 PR runs
random.seed(42)
for v in [1, 2, 3]:
    conn.execute(
        "INSERT INTO prompts VALUES (?, ?, ?, ?, ?)",
        (f"prompt_v{v}", v, f"template_v{v}", "gpt-4o", "2026-10-01")
    )

for i in range(200):
    conn.execute(
        "INSERT INTO eval_set VALUES (?, ?, ?, ?, ?)",
        (f"eval_{i}", f"query_{i}", f"chunk_{i}", f"answer_{i}",
         random.choice(['easy', 'medium', 'hard']))
    )
conn.commit()
print(f"  Seeded 3 prompt versions, 200 eval queries")

# Simulate 3 PR runs
print()
print("-" * 70)
print(f"{'PR':<6} {'Version':<10} {'Recall@8':<10} {'Judge':<8} {'Hallu':<8} {'Cost':<8} {'Verdict'}")
print("-" * 70)

PR_RUNS = [
    # (pr, version, recall, judge, hallu, cost, expected_verdict)
    (101, 2, 0.87, 4.3, 0.02, 0.014, "ship"),         # good: ship
    (102, 3, 0.79, 3.5, 0.08, 0.013, "block"),         # bad recall: block
    (103, 3, 0.85, 4.0, 0.06, 0.014, "manual_review"), # borderline: review
]

# Thresholds
RECALL_THRESHOLD = 0.85
JUDGE_THRESHOLD = 4.0
HALLU_THRESHOLD = 0.05

for pr, version, recall, judge, hallu, cost, expected in PR_RUNS:
    # Decision logic
    if recall < RECALL_THRESHOLD:
        verdict = "block"
        reason = f"Recall@8 {recall} < {RECALL_THRESHOLD}"
    elif judge < JUDGE_THRESHOLD:
        verdict = "block"
        reason = f"Judge {judge} < {JUDGE_THRESHOLD}"
    elif hallu > HALLU_THRESHOLD:
        verdict = "block"
        reason = f"Hallucination {hallu} > {HALLU_THRESHOLD}"
    else:
        verdict = "ship"
        reason = "all metrics green"

    print(f"  PR {pr:<3} v{version:<8} {recall:<10.2f} {judge:<8.1f} {hallu:<8.1%} ${cost:<7.4f} {verdict}")
    conn.execute(
        "INSERT INTO eval_run VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (f"run_{pr}", version, pr, "2026-10-17", recall, judge, hallu, cost, verdict)
    )

conn.commit()

# ════════════════════════════════════════════════════════════════
# LLM-AS-JUDGE CALIBRATION (the AI-native core)
# ════════════════════════════════════════════════════════════════
print()
print("=" * 70)
print("LLM-AS-JUDGE CALIBRATION (the AI-native core)")
print("=" * 70)
print("""
LLM-as-judge is the cheap eval. But it's NOT free. Three problems:

1. INTER-RATER AGREEMENT
   GPT-4 vs human: ~85% agreement. NOT 100%.
   If judge says 4.5 but humans say 3.5, you're shipping regression.
   The defense: calibrate judge against human-labeled examples.

2. PROMPT SENSITIVITY
   'Rate 1-5' gives different distributions than 'Rate excellent/good/fair/poor'.
   Lock the judge prompt. Re-calibrate if you change it.

3. BIAS
   Judge prefers longer answers. Judge prefers GPT-style tone.
   Judge scores itself higher than other models.
   The defense: blind the judge to model identity.
""")

# Simulate judge vs human agreement
print("\nJudge vs human agreement on 50 calibration examples:")
random.seed(42)
agreements = {'agree': 0, 'judge_higher': 0, 'judge_lower': 0}
for i in range(50):
    human_score = random.choice([1, 2, 3, 4, 5])
    # Judge tends to be +0.5 higher
    judge_score = max(1, min(5, human_score + random.choice([-1, 0, 0, 0, 1, 1])))
    diff = judge_score - human_score
    if diff == 0:
        agreements['agree'] += 1
    elif diff > 0:
        agreements['judge_higher'] += 1
    else:
        agreements['judge_lower'] += 1

total = sum(agreements.values())
print(f"  Agree:          {agreements['agree']}/{total} ({100*agreements['agree']/total:.0f}%)")
print(f"  Judge higher:   {agreements['judge_higher']}/{total} ({100*agreements['judge_higher']/total:.0f}%)")
print(f"  Judge lower:    {agreements['judge_lower']}/{total} ({100*agreements['judge_lower']/total:.0f}%)")
print(f"  => Judge has positive bias of {agreements['judge_higher'] - agreements['judge_lower']} examples")
print(f"  => Calibration: subtract 0.5 from judge score before comparing to threshold")

# ════════════════════════════════════════════════════════════════
# THE 4 NEVER-DOS (the AI-native cardinal sins)
# ════════════════════════════════════════════════════════════════
print()
print("=" * 70)
print("THE 4 NEVER-DOS (the AI-native cardinal sins)")
print("=" * 70)
print("""
1. NEVER ship a prompt change without running the eval set
   The most common AI-native bug. Engineer tweaks a prompt,
   pushes to prod, satisfaction drops 5pp the next day.

2. NEVER trust LLM-as-judge without calibration
   Judge is biased. Judge prefers longer answers. Judge scores
   its own family higher. If you don't calibrate, you ship
   regressions the judge says are improvements.

3. NEVER overwrite the eval set
   Eval set is the ground truth. If you add bad labels, the
   eval is meaningless. Versioned like code, append-only.

4. NEVER skip the canary
   Eval set says "ship". Real users say otherwise. The 1%
   canary catches distribution shift the eval set missed.
   Skipping the canary is gambling with 1B users.
""")

# ════════════════════════════════════════════════════════════════
# THE PRODUCTION DEPLOY PIPELINE
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("THE PRODUCTION DEPLOY PIPELINE (the AI-native CI/CD)")
print("=" * 70)
print("""
PR opens
   |
   v
Run eval set (5 min, $0.50)
   |
   +-- metrics regressed? --> BLOCK PR, require changes
   |
   v
Merge to main
   |
   v
Deploy to staging (10 min)
   |
   v
Shadow canary: 1% traffic for 24h
   |
   +-- any metric regressed? --> auto-rollback
   |
   v
Promote to 10% (24h)
   |
   v
Promote to 50% (24h)
   |
   v
Promote to 100%
   |
   v
Watch dashboard for 7 days (auto-rollback if regression)

Total time from PR to 100%: ~5 days
Total cost per PR: $5 (eval) + $50 (LLM judge calibration)
""")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("L6 ANSWER (when they ask 'how do you ship LLM changes safely?')")
print("=" * 70)
print("""
Q: "You ship LLM-powered features to 1B users. How do you make sure
    a prompt change doesn't break the product? When is LLM-as-judge
    trustworthy enough to ship without human review?"

A: "AI-native means the eval is in the deploy loop, not after.

THE 4 LAYERS (all required, none optional):

1. PROMPT VERSIONING
   Every prompt has a version. Every trace records the version.
   prompts(prompt_id, version, template, model, created_at)
   traces(prompt_version REFERENCES prompts(version))
   Without this, you can't even attribute a regression to a change.

2. EVAL SET IN CI
   PR opens -> CI runs the eval set against the new prompt.
   Eval set: 1000 labeled (query, expected) pairs, versioned,
   append-only, never overwritten.
   Block the merge if: Recall@8 < 0.85, judge < 4.0/5,
   hallucination > 5%.
   This is the cheap gate. $0.50 per PR. 5 min runtime.

3. SHADOW CANARY
   New prompt serves 1% of traffic in parallel with old prompt.
   Compare 5 metrics: Recall@8, judge score, p95 latency, cost
   per query, user satisfaction.
   Auto-promote at 24h if all green. Auto-rollback if any
   metric regresses more than 5 percentage points.
   The canary catches distribution shift the eval set missed.

4. AUTO-ROLLBACK
   Watch the production dashboard for 7 days post-promotion.
   If satisfaction drops > 3pp OR p95 > 1s OR hallucination
   > 0.1% -> automatic rollback to previous prompt version.
   Rollback is a config push, not a re-deploy. < 5 min.

ON LLM-AS-JUDGE (the AI-native critical question):
   LLM-as-judge is the cheap eval. It's NOT free.

   Three problems:
   - Inter-rater agreement with humans is ~85%, not 100%
   - Prompt sensitivity: 'rate 1-5' vs 'rate excellent/poor'
     gives different distributions
   - Bias: judge prefers longer answers, GPT-style tone,
     and scores its own family higher

   The defense: calibrate. Run 50 human-labeled examples
   through the judge. Measure agreement. Subtract systematic
   bias. Re-calibrate any time the judge prompt changes.

   The L6 line: 'LLM-as-judge is trustworthy when its
   calibration curve is documented, its agreement with
   humans is measured, and its blind spots are known.
   Untill all three, ship changes behind a 1% canary.'

THE CARDINAL SIN: ship a prompt change without running the eval set.
  - 80% of LLM regression incidents trace to 'we changed a prompt
    and didn't measure'
  - The eval set is not optional. It's the safety net.
  - The eval set is not the judge. The eval set is the ground truth
    the judge is calibrated against.

THE L6 POSITION (use this verbatim):
  'AI-native engineering is the discipline of treating LLM outputs
   as production code: versioned, evaluated, canaried, and
   rollbackable. The eval set is the test suite. The judge is the
   linter. The canary is the staging environment. Without all four,
   you're shipping LLM changes on hope, not measurement.'
""")
