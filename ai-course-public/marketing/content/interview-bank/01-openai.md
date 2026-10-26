# 1. OpenAI

> **Hero image spec:** 1400×788 px. Mood: editorial-technical (Stripe Press meets MIT Tech Review). Composition: the company name + 1 signature visual from the company's domain (transformer blocks for OpenAI). Color: company brand color as accent (teal-green). Headline on image: "OpenAI / AI Engineer / 2026".

> **TL;DR:** The OpenAI loop runs 5 stages and kills ~98% of candidates. The gate is the coding round — but not because the problem is hard. It's a *small system* you'd actually build on the job (e.g., directed social graph with snapshot queries), and you'll get 2-3 extensions layered on top in 45-60 minutes on CoderPad. The candidate who wins treats it like production code: tests at every step, names trade-offs out loud, and can list the 3 ablations they *didn't* run on their ML project. The ones who lose either LeetCode-optimize, defend every design choice, or can't name a single bet they'd disagree with the company on.

```
Recruiter (80%) → Hiring manager (50%) → Skills (40%) → Final loop (25%) → Committee (60%) → Offer
```

- **Role:** AI Engineer
- **Tech stack:** Python, PyTorch, CUDA, Triton, vLLM, TensorRT-LLM, CoderPad
- **Comp band:** $251K-$1.89M total comp (L2-L7 SWE) | RSUs 4-year, **6-month cliff** (changed from 12mo in Apr 2025)
- **Cumulative pass rate:** ~1-2% (analogy estimate — OpenAI publishes no funnel data)

## How to use this doc

Read it three times, in this order:

1. **First read (60 min, straight through):** absorb the structure. Don't memorize answers — internalize the *frame* (small system, named thresholds, ablations-not-defended).
2. **Second read (3-4 hours, with a friend):** whiteboard every answer out loud. If you can't finish in 90 seconds, you don't know it. Time yourself on the coding answers.
3. **Third read (1 hour, before the loop):** skim the pre-mortem and the decision tree. Sleep on it.

If you only have 1 hour: skip to "If you only have 1 hour" at the bottom.

## Level calibration (do this BEFORE the recruiter call)

The recruiter is going to ask your years and your comp. If you give wrong numbers, you get routed to the wrong loop and there's no recovery. The committee can downgrade you even if every interviewer said yes.

**Self-assessment rubric (be honest, this is just for you):**

| Signal | L3 | L4 | L5 | L6 | L7 |
|--------|----|----|----|----|----|
| Years of post-undergrad experience | 2-3 | 4-5 | 6-8 | 8-12 | 12+ |
| Owns a system end-to-end? | Component | Full system | Multi-system | Org-wide | Multi-org |
| Has shipped to >1M users? | No | Yes | Yes | Yes | Yes |
| Has been on-call for the system? | Shadowed | Yes | Yes | Yes (built the runbook) | Yes (built the on-call practice) |
| Has mentored others? | No | 1-2 | 3-5 | 5-10 | 10+ |
| Has technical writing / public artifacts? | 1-2 | 3-5 | 5+ | Many | Defines the org's voice |
| Has disagreed with senior leadership and won? | No | Once | A few times | Regularly | Routinely |

**The litmus test for L4 vs. L3:** can you defend why you'd be effective *on day 1* with no ramp-up? If yes, L4. If "with 2-3 months of ramp-up," L3.

**The litmus test for L5 vs. L4:** can you point to a system you designed (not just built) that other teams have adopted? If yes, L5. If "I built it for my team and they use it," L4.

**The litmus test for L6 vs. L5:** have you been the tech lead for a 6+ month project that crossed team boundaries and you had to negotiate scope, timeline, and design with other teams? If yes, L6.

**Negotiating up vs. down:** if you calibrate to L4 but the recruiter pushes for L3, *push back once* with a specific scope claim. If they don't budge, accept L3 and crush the loop — the committee can promote mid-loop if your signal is strong enough (rare but real). Never accept a downlevel that wasn't offered.

## What the loop actually tests

Most candidate interviews assume OpenAI is testing "can you code ML." It's not. It's testing five things, in this order of weight:

1. **Can you build something a teammate would want to merge?** (coding)
2. **Can you talk about a project like you actually built it?** (project deep-dive)
3. **Do you have a specific, falsifiable bet about AI?** (mission fit)
4. **Would I want to be stuck in a room debugging with you at 2am?** (behavioral)
5. **Can you write Python faster than the interviewer?** (speed, implicitly)

If you optimize for #1 and #3, you pass. If you optimize for "sounding smart," you don't.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, comp, role fit | 1 week | ~80% advance |
| 2. **Hiring manager** | Project deep-dive, mutual fit | 1-2 weeks | ~50% advance |
| 3. **Skills assessment** | Pair-coding, take-home, or technical test | 2 weeks | ~40% advance |
| 4. **Final loop (4-6 hrs)** | Coding → system design → project talk → behavioral → optional agentic round | 1-2 days | ~25% advance (illustrative) |
| 5. **Decision + offer** | References checked; no negotiation, but level calibration matters | 3-7 days (loop-to-decision); 6-8 weeks (full loop) | — |

> **Note on pass rates:** OpenAI publishes no funnel data, and the exact per-stage percentages above are illustrative (drawn from industry benchmarks in the 30-60% range). The ~1-2% cumulative is an order-of-magnitude estimate by analogy to Google's leaked data — not measured for OpenAI specifically.

## Stage 1: Recruiter screen (30 min)

The recruiter is calibrating your level. Two things go wrong here: (a) you inflate your title, (b) you don't have a specific reason for OpenAI. Both get you routed to the wrong loop.

### Q1.1: "Tell me about your background"
**Answer:** I'm a senior ML engineer — 6 years in production, not 3. Most recently I built the inference platform at [X]: multi-tenant, served 50M requests/day, cut p99 latency from 800ms to 180ms by switching from naive batching to continuous batching with vLLM. The project that maps to OpenAI is the RLHF stack I built at [Y] — SFT, reward model, PPO, 3 ablation rounds. I want to work on inference efficiency at the frontier, and OpenAI's cost-curve bet is the one I want to test.
**Tip:** Years of experience, not title. "Senior" without the years is a downlevel flag.

### Q1.2: "Why OpenAI, specifically?"
**Answer:** I'm skeptical of pure-RLHF alignment — I'd want to test whether deliberative alignment (the o-series approach) actually generalizes beyond the safety policy the model was trained against, or whether it just memorizes a list of rules. I believe in the inference cost-curve story: 10× cheaper inference unlocks a product category that doesn't exist yet — DevDay 2026 made this explicit with GPT-6.1 Sol at 1/5 the per-token cost. The first is where I'd want to be a skeptic; the second is where I'd want to be a builder.
**Tip:** A specific bet + a specific test + a specific disagreement beats "I want to work on AGI" every time. If you can't disagree with the company, you don't understand it. Bonus points: name a current bet (Codex / agents, deliberative alignment, GPT-6 series) and explain why you'd test it.

### Q1.3: "What's your comp?"
**Answer:** I'm targeting L3-L4 based on years of experience and scope. Total comp in the $400-600K range is what I'd expect to see for the level. I'm flexible on the mix — I'd take more equity over base if the level is right.
**Tip:** State a level, not a number. Let the recruiter calibrate you; don't anchor them.

**2026 L-level reference (Levels.fyi, median total comp):**
- L3: ~$400-500K
- L4: ~$770K (range $595K-$1.08M)
- L5: ~$850K-$1.0M
- L6: ~$1.1-1.4M (staff)
- L7: up to $1.89M+ (principal/fellow-track)

If you can't defend why you belong at the L4 line on the dot, the recruiter will route you to L3 — and you will not get bumped up after the loop.

## Stage 2: Hiring manager / project deep-dive (60 min)

This is two interviews in one: a coding problem and a project walkthrough. The HM round is where OpenAI decides if you actually built what your resume claims. The project deep-dive is the make-or-break signal here — not the coding problem. (Note: in some pipelines the project deep-dive appears as a separate onsite round with a 30-min presentation format. Both are real; ask your recruiter.)

### Q2.0: "Walk through your most significant project, ablations, and what you didn't test"
**Answer:** I built a retrieval-augmented generation pipeline that hit competitive performance on HotpotQA. The setup: dense retriever (DPR) over Wikipedia, cross-encoder reranker, generator (7B). The interesting finding: the reranker was where the wins came from — without it, we were at the SOTA baseline; with it, we pulled ahead on multi-hop questions. (Note: at 2026 SOTA ceilings of ~70-80% on HotpotQA, a 4-point jump from a single reranker is implausible — frame as "competitive on multi-hop" or use a benchmark where the gain is realistic, e.g., BEIR, a domain-specific QA set, or a private eval.)

Three ablations I didn't run, in priority order:
1. **OOD generalization**: same model on arXiv abstracts vs. Wikipedia. Tells me whether the win generalizes beyond the training distribution. I'd run this first because it's the most likely place the result doesn't transfer.
2. **Data efficiency curve**: with 10× less training data, what's the gap to the full-data baseline? Tells me whether the approach is data-hungry or sample-efficient.
3. **Baseline swap**: against ColBERT instead of DPR. Isolates whether the win is from reranking in general or from DPR specifically.
**Tip:** Naming the 3 things you didn't test beats defending everything. The interviewer is testing whether you know the limits of your own work.

## Stage 3: Technical phone screen (60 min)

The phone screen is a coding problem on CoderPad, typically 45-60 min. Token bucket / rate limiter is one of the common prompts (alongside LRU cache, mini KV store, scheduler, in-memory DB with TTL). The 2026 rubric is graded on four things, in roughly this order: (1) working happy path, (2) lazy refill timing correctness, (3) named trade-offs in the extension (centralized Redis vs. local+sync, fairness across tenants), (4) clean OOP for multi-bucket composition. Tests are appreciated but secondary to trade-off articulation.

### Q2.1: "Implement a token bucket rate limiter, then extend to per-user + per-tenant limits"
**Answer:**
```python
import time
from collections import defaultdict

class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate, self.capacity = rate, capacity
        self.buckets = defaultdict(lambda: {"tokens": capacity, "ts": time.monotonic()})

    def allow(self, key, n=1):
        b = self.buckets[key]
        now = time.monotonic()
        # Lazy refill — no background thread, no locks needed
        b["tokens"] = min(self.capacity, b["tokens"] + (now - b["ts"]) * self.rate)
        b["ts"] = now
        if b["tokens"] >= n:
            b["tokens"] -= n
            return True
        return False


def test_basic_rate_limit():
    tb = TokenBucket(rate=10, capacity=10)
    assert tb.allow("alice")  # first request
    for _ in range(9):
        assert tb.allow("alice")
    assert not tb.allow("alice")  # bucket drained
    assert tb.allow("bob")  # separate key, separate bucket
```

For per-tenant extension: hierarchical keys (`tenant:user`), check tenant bucket first, refill user bucket from tenant bucket on hit. The grader wants named trade-offs and named thresholds — not 200 lines.
```python
# Trade-off named out loud:
# - Lazy refill beats a background timer (no thread, no lock contention)
# - defaultdict means cold keys start full — usually fine, sometimes wrong
#   (denial-of-service: a flood of new keys never throttles). I'd switch to
#   a real LRU cache at >1M active keys.
# - Per-tenant extension: hierarchical keys, tenant-bucket check first.
#   Trade-off: single-process dict is fast, but doesn't share state across
#   gateway instances. Switch to Redis with atomic INCR + EXPIRE at
#   >10K req/sec per instance.
```
**Tip:** The 2026 rubric is graded on (1) working happy path, (2) lazy refill timing correctness, (3) named trade-offs in the extension (centralized Redis vs. local+sync, fairness across tenants), (4) clean OOP for multi-bucket composition. Tests are appreciated but secondary to trade-off articulation. Write the smallest correct version first, then extend.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding

This is the round people fail most. Not because the problem is hard — it's a system you'd actually build on the job. People fail because they LeetCode-optimize, write 200 lines, skip tests, and can't extend it.

OpenAI's coding round is **45-60 min on CoderPad**, and the format is consistent across 2026 reports: the interviewer hands you a base spec and layers **2-3 follow-up extensions** that grow in scope (TTL, sharding, concurrency, time-travel queries). The grader is **live the whole time** — watching your process, not just the final code. Tests are part of the rubric, but the explicit "tests graded at every step" claim is overstated; what's actually graded is whether you write tests proactively and whether the interviewer trusts your code at each checkpoint.

Common problem variants reported in 2026: LRU cache, rate limiter / token bucket, resumable iterator, in-memory KV store with TTL, time-travel DB, **directed social graph with snapshot queries** (a real example — but one of many, not canonical), webhook delivery, GPU scheduler, credit-balance replay, spreadsheet formula evaluator.

### Q3.1.1: "Build a directed social graph with snapshot/version queries"
**Answer:** The right structure is an adjacency list of immutable versions keyed by timestamp. Mutations append a new version, linked to the parent. Reads do a binary search over the version array to find the right snapshot.

```python
import time
from typing import Optional

class VersionedGraph:
    def __init__(self):
        self.versions = []  # list of {ts, edges: dict[node, set[neighbor]]}

    def add_edge(self, u, v):
        prev = self.versions[-1].edges if self.versions else {}
        new_edges = {k: set(v) for k, v in prev.items()}
        new_edges.setdefault(u, set()).add(v)
        self.versions.append({"ts": time.monotonic(), "edges": new_edges})

    def followees_at(self, node, ts) -> set:
        # Binary search for the right version
        lo, hi = 0, len(self.versions) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.versions[mid]["ts"] <= ts:
                lo = mid
            else:
                hi = mid - 1
        return self.versions[lo]["edges"].get(node, set())


def test_versioned_graph():
    g = VersionedGraph()
    g.add_edge("alice", "bob")
    t1 = time.monotonic()
    time.sleep(0.01)
    g.add_edge("alice", "carol")
    t2 = time.monotonic()
    # At t1, alice follows bob only
    assert g.followees_at("alice", t1) == {"bob"}
    # At t2, alice follows both
    assert g.followees_at("alice", t2) == {"bob", "carol"}
```

OpenAI extends this 2-3 times — usually (1) add delete_edge, (2) add `followers_at`, (3) add a "diff between two timestamps" query. Tests at every extension.
**Tip:** The grader isn't reading your code — they're watching your process. Talk through the structure before you code. Write the test before the function. Name the trade-off (here: O(log n) reads vs. O(1) writes with copy-on-write).

### Q3.1.2: "Implement DPO loss with ties"
**Answer:**
```python
import torch
import torch.nn.functional as F

def dpo_loss(policy_chosen_logps, policy_rejected_logps,
             ref_chosen_logps, ref_rejected_logps,
             beta=0.1):
    chosen_logratios = policy_chosen_logps - ref_chosen_logps
    rejected_logratios = policy_rejected_logps - ref_rejected_logps
    logits = beta * (chosen_logratios - rejected_logratios)
    return F.binary_cross_entropy_with_logits(logits, torch.ones_like(logits))
```

For ties (when two completions are equally preferred, i.e., the same response appears on both sides of the preference): the log-ratio is 0, contributing nothing to the loss. The original Rafailov et al. 2023 paper doesn't define a special case — standard practice is to either drop ties from training or keep them as zero-loss examples. There is no canonical "weighted averaging over separate preferred/dispreferred pairs" convention for ties in the base DPO paper; that pattern describes pairwise ranking with multiple comparisons per prompt, which is different.
**Tip:** Derivations on the whiteboard are graded on correctness, not memorization. If you can't derive it, say "I can't derive this from scratch right now, here's what I remember and what I'd verify."

### Round 3.2: System design

The system design round signals what they want up front. "Don't focus on the model" = focus on serving, caching, cost. If they say "focus on the model" — actually focus on the model. They're telling you what they're hiring for.

### Q3.2.1: "Design a multi-tenant LLM inference platform with cost attribution"
**Answer:** Three layers: API gateway (auth, tenant resolution, rate limit) → inference router (model selection, request batching, queueing) → serving (vLLM or TensorRT-LLM with continuous batching).

Cost attribution: token-counting middleware at the gateway, writes per-tenant metrics to Prometheus. Nightly job reconciles against Stripe metered billing. Trade-off: per-request overhead vs. accuracy. Sample 1/10 requests in detail, extrapolate — full accounting is too expensive at scale.

Concrete numbers I'd name:
- p99 latency budget: 500ms for short prompts, 2s for long
- KV cache memory: ~80GB at 8B model, batch=32
- Cost target: < $0.001 per 1K tokens at the GPU level
**Tip:** Name the threshold where you'd switch systems. "If we're at >100K req/sec, we'd move from Prometheus to a streaming aggregator."

### Q3.2.2: "Design a webhook delivery system with at-least-once semantics"
**Answer:** Durable queue (Kafka or SQS) + per-tenant ordering key + exponential backoff with jitter + dead-letter after 5 retries. Receiver uses event ID for idempotency.

The right pick over Kafka: Postgres LISTEN/NOTIFY if scale < 100K/sec. The threshold to switch from Postgres to Kafka is around 100K events/sec sustained — below that, the cost of operating Kafka is worse than the cost of Postgres working harder.
**Tip:** Name the threshold. Always.

### Round 3.3: ML depth (technical, not project walkthrough)

### Q3.3.1: "Walk me through how you'd take a 7B base model from base to a deployed, aligned model that handles a tool-use API. What are the trade-offs at each step?"
**Answer:** Four stages with named trade-offs at each:
1. **SFT on instruction data** — pick a dataset (FLAN, OASST, or internal curated), 2-3 epochs, watch for overfitting on small data. Trade-off: data quality vs. quantity.
2. **Reward model training** — preference data from human raters (or GPT-4-as-judge if scale matters more than quality). Pairwise comparisons, not scalar ratings. Trade-off: rater quality vs. rater throughput.
3. **RLHF (or DPO)** — PPO is the workhorse; DPO is the simpler alternative that doesn't need a separate reward model at training time but inherits DPO's length bias. Trade-off: alignment quality vs. training complexity.
4. **Tool-use integration** — fine-tune on tool-use trajectories, or use ReAct-style prompting at inference. Trade-off: model "knows" the API vs. agent framework handles it.
**Tip:** Name the trade-off and the threshold where you'd switch. "If tool-call accuracy < 90% I'd switch from prompt-only to fine-tuned."

### Round 3.4: Behavioral

The behavioral round is graded on specificity, not STAR format. Generic STAR answers lose. Specific, time-boxed, falsifiable stories win.

### Q3.4.1: "Tell me about a time your research contradicted your hypothesis"
**Answer:** I hypothesized DPO would beat PPO on a 7B alignment task. Setup was standard: SFT base, GPT-4 as judge for reward model, 3 epochs.

Result: DPO won on reward-model score but lost on human eval because of verbosity — DPO outputs were noticeably longer, and the longer outputs scored higher on the reward model but worse with humans. (Note: DPO's length bias is a well-documented pattern — Singhal et al. ACL Findings 2024 and the EMNLP 2024 "Eliminating Biased Length Reliance" paper both quantify it. Exact length inflation varies by dataset/model; 20-60% appears in the literature, no canonical "40%" figure exists. Use a number from your own experiments; don't cite a specific literature value if you don't have it.)

Fix: added a length penalty to the reward model (normalized score by token count), retrained. DPO then won both. Park et al. 2024 ("Length-Controlled DPO") is the cleaner published fix if you want to cite something.

What I learned: optimize against the metric that matches the eval. The RM was wrong, not the method.
**Tip:** Specific numbers (from your own experiments). Specific time-box ("3 epochs"). Specific lesson. "I learned the importance of evaluation" loses.

### Q3.4.2: "A time you were wrong"
**Answer:** I believed quantization below 4-bit was unusable — I'd seen the perplexity spikes and assumed they correlated with downstream task quality. I was wrong. The Frantar et al. GPTQ paper (ICLR 2023) showed 3-bit is *close* to 4-bit on most downstream tasks even with a visible perplexity gap — within ~1 point on LAMBADA, PIQA, and StoryCloze, though ARC tasks show 2-3 point drops. The bigger lesson: at low bit-widths, perplexity and task quality diverge — perplexity "underestimates" true model quality.

I now test at every bit-width (8, 4, 3, 2) before deciding, and I separate "perplexity went up" from "task quality went down." If I'm picking a method today, AWQ (Lin et al. 2023) generally beats GPTQ at 3-4 bit, but GPTQ is still the baseline I measure against.
**Tip:** Show belief updating, not failure. "I was wrong and learned a lesson" is a story about a lesson. "I was wrong, here's what I changed about how I work" is a story about you.

## Stage 4: Decision committee

After the loop, the packet goes to a decision committee whose exact composition OpenAI does not publish (mechanics are "opaque" in public reports). Treat the common claim of "5-8 staff+ engineers" as a community estimate rather than a verified fact. The committee looks for three things:

1. **A coherent technical narrative across rounds.** If your coding round says "systems thinker" and your project says "pure researcher," you get downgraded. The narrative has to be consistent.
2. **Specific mission-fit evidence.** Generic "I want AGI" doesn't count. A specific bet ("I'd want to test whether constitutional AI closes the gap on TruthfulQA") does.
3. **A "level" consensus.** L3 vs. L5 is the most-disputed call. The committee can — and often does — override an interviewer's recommendation.

The committee can downgrade you even if every interviewer said yes. Average wait: 3-7 days after the loop (longer if the level is debated); full recruiter-to-offer is 6-8 weeks.

## Stage 5: Offer

OpenAI does not negotiate salary in the traditional sense — the offer reflects the calibrated level. The play: get the level right in the recruiter call. If you anchor to your current title and the committee disagrees, you get downleveled and there's no recovery.

- **Equity:** 4-year vest, **6-month cliff** (changed from 12mo in April 2025 for new hires), 25% per year after cliff.
- **Relocation + immigration support** is real and well-funded.
- **Sign-on bonus** is rare but exists for senior candidates with competing offers — and only when the competing offer is at the same level. Context: in Aug 2025, OpenAI issued ~$1.5M retention grants to ~1,000 staff specifically to counter Meta poach attempts; spot multi-million-dollar sign-ons appear in similar counter-offer situations. Standard hires don't get sign-on.
- **The negotiation lever is the level, not the number.** If you try to negotiate base up, you lose the rest.
- **2025 for-profit restructuring:** PPUs converted to conventional RSUs at the Oct 2025 $500B tender (~$6.6B raised). The nonprofit OpenAI Foundation retained a ~$130B stake (Forbes, Apr 2026). This materially changed grant valuation and shifted more weight to performance-based equity at the top.
- **Immigration:** H-1B, O-1A (for top researchers), and Green Card sponsorship is heavy — but as of Aug 2026, OpenAI settled a DOJ lawsuit for $3.2M over PERM recruitment practices, and the DOJ now has oversight of green-card sponsorships. Expect standard Big Tech immigration support, not unusually generous.

The candidate who tries to negotiate base loses the rest.

## Tips for the OpenAI loop

- **Coding is a small system, not LeetCode.** Build it like a real codebase: tests at every step, error handling, named trade-offs. The grader is watching your process, not reading your code. Expect 2-3 extensions in 45-60 min.
- **System design signals what they want.** "Don't focus on the model" = focus on serving, caching, cost. If they say focus on the model, focus on the model. They're telling you what they're hiring for.
- **"I don't know" is a feature.** Name the 3 things you don't know about your own work. The candidate who says "I tested everything" loses to the candidate who says "here's what I didn't test and why."
- **AI tools vary by round — OpenAI's own guide says so explicitly.** Quote: *"Expectations for AI and other tools vary by interview: some formats intentionally allow them, while others are designed to assess your independent problem-solving without AI tools."* Default action: ask your recruiter. The agentic round (when present) requires you to drive a coding agent live and is graded on your *supervision judgment* — whether you catch the tool's mistakes, redirect when it goes off-track, and verify output. Letting the agent run unsupervised is the red flag, not a planted bug.
- **Mission fit is one of ~6 evaluated signals, not a separately weighted round.** Per OpenAI's official interview guide, mission alignment sits alongside expertise, collaboration, communication, openness to feedback, and engineering quality — no published weights, but it can veto. "I want AGI" loses. "I want to test whether deliberative alignment generalizes beyond the safety policy the model was trained against" wins. The guide is explicit: it requires "a substantive connection to the role, not generic enthusiasm."
- **Inflating experience downlevels you.** Be honest about years. The recruiter has a calibration chart; lying on it routes you to the wrong loop.
- **The recruiter calibrates.** Don't anchor to your current title. Anchor to your years and your scope.
- **Specific numbers beat specific words.** "Cut p99 latency by 4×" beats "improved performance." Every claim needs a number.
- **The behavioral round is not STAR.** It's "tell me a specific story with a falsifiable result." Generic STAR answers lose.

## Real candidate report

> *"The coding question asked me to implement a directed social graph that supported real-time versioning with snapshot queries. It wasn't a LeetCode hard — it was a small system I'd actually have to build on the job. I extended it three times as the interviewer added requirements. Tests at every step. The interviewer spent more time watching me write tests than watching me write code — that's when I knew I was on the right track."*
> — [r/OfferEngineering, OpenAI Senior SWE Interview (Aug 2026)](https://www.reddit.com/r/OfferEngineering/comments/1vdpjty/openai_senior_swe_interview/)

---

# Active prep: turn this doc into a study system

Reading the doc twice doesn't get you in. The candidate who wins has done the *active* work — filled in the blanks, drilled the calibrations, white-boarded under time pressure. Everything below is that work. Do it.

## Spaced repetition schedule

**Day 1 (2-3 hours):**
- Read the whole doc top to bottom, no notes
- Fill in every blank template below without looking at the answer
- Do every calibration drill, timed
- Whiteboard the 3 system designs (token bucket, multi-tenant LLM, webhooks) — code, not just talk

**Day 3 (90 min):**
- Re-fill the templates, from memory
- Redo the calibration drills you missed
- Read every "failure mode" section. For each one, write down: "Have I done this? How would I catch myself doing it?"

**Day 7 (60 min):**
- Skim the doc once
- Do one mock coding round with a friend (45 min, CoderPad, no AI)
- Do one mock behavioral round with a friend (30 min, no notes)
- For each system design prompt, time your outline (5 min) and your deep dive (25 min)

**Day 30 (30 min):**
- Skim the failure modes + pre-mortem
- If you have a scheduled loop: re-read "Loop day logistics" the night before

**Day 1 of loop: morning of, 30 min:**
- Skim the decision tree for the coding round
- Skim the loop-day logistics
- No new material. Trust the prep.

## Blank-answer templates

For every question below, fill in the blank with YOUR answer. If you can't, that's a gap. Don't peek at the model answer until you've tried.

### T1.1: Background (90 sec)
- Years of experience: ___
- Most recent role, scope, numbers: ___
- One project that maps to OpenAI: ___
- Why this role, specifically: ___

### T1.2: Why OpenAI (90 sec)
- One specific bet I disagree with OpenAI on: ___
- The test I'd run to settle it: ___
- One bet I'm aligned with: ___
- Why I'd be a builder on it: ___

### T1.3: Comp target
- Level: L___
- Total comp target: $___
- Mix preference: base-heavy / equity-heavy / even
- Competing offers (if any): ___

### T2.0: Project walkthrough (5 min, the biggest single moment in the loop)
- The system I built: ___
- The result, with a number: ___
- Why the result matters: ___
- The 3 ablations I didn't run, in priority order:
  1. ___
  2. ___
  3. ___
- The one I'd run first and what I'd expect: ___

### T2.1: Token bucket (45-60 min on CoderPad)
- Data structure: ___
- Refill strategy + why: ___
- Test cases I'll write before coding: ___
- Per-tenant extension: ___
- The threshold where I'd switch to a different system: ___

### T3.1.1: Directed social graph with snapshot queries
- Data structure + why: ___
- Read complexity: ___
- Write complexity: ___
- Test cases: ___
- The 2-3 extensions I'd pre-think: ___

### T3.1.2: DPO loss
- The formula, from memory: ___
- What ties mean in this context: ___
- How I'd handle ties: ___

### T3.2.1: Multi-tenant LLM inference with cost attribution
- 3 layers, named: ___
- Where cost attribution lives: ___
- The 1 trade-off I'd name: ___
- The 3 numbers I'd state (p99 latency, cost/1K tokens, throughput/GPU): ___

### T3.2.2: Webhook delivery with at-least-once semantics
- The queue I'd pick and why: ___
- The idempotency strategy: ___
- The retry policy: ___
- The threshold where I'd switch from Postgres to Kafka: ___

### T3.4.1: Research contradicted hypothesis
- The hypothesis: ___
- The setup (1 sentence): ___
- The result, with a number: ___
- The contradiction: ___
- The fix: ___
- What I learned: ___

### T3.4.2: A time you were wrong
- The belief I held: ___
- Why I held it: ___
- What changed my mind (a paper, a result, an argument): ___
- What I changed about how I work: ___

## Failure mode analysis (and what makes the people who fail)

For each question, the 2-3 ways candidates fail. Self-diagnose: "Have I ever done this? How would I catch myself?"

**The candidates who fail share 5 patterns. Internalize these so you can spot them in real time.**

### Pattern 1: The "I just need to sound smart" candidate

You answer every question like you're writing an essay for a journal reviewer. Symptom: your sentences are long, your hedges are many, and you never state a number. The interviewer can't tell if you built anything or just read about it.

**How they fail:** they confuse depth with verbosity. They defend every design choice as if attacked. They never say "I don't know" because they think it sounds weak. They never name a threshold because they think it sounds prescriptive.

**What wins instead:** terse, specific, with a number. "Cut p99 latency from 800ms to 180ms by switching from naive batching to continuous batching. The trade-off was 2× memory per request, which we could afford because p99 was the binding constraint." That wins. "We optimized our inference pipeline by implementing various batching strategies" loses.

### Pattern 2: The "I've seen this on LeetCode" candidate

You recognize the prompt and reach for the optimal solution immediately. Symptom: you finish the coding round in 20 min with no tests, no comments, no trade-offs. The interviewer has 25 min of dead air.

**How they fail:** they treat the interview as a speed test. They write the cleverest code instead of the most readable code. They never think out loud because they assume the interviewer can read their code.

**What wins instead:** boring code with tests. "I'll use a defaultdict for the buckets. Here's why: it's the simplest structure that meets the read/write requirements, and refactoring to a real LRU is one line if we hit the cold-key DoS edge case." That wins.

### Pattern 3: The "I'm too senior to be tested" candidate

You act like the interview is beneath you. Symptom: you answer quickly, you don't write tests ("any senior engineer would have those"), you push back on the prompt ("in production, I'd use Redis"), you get defensive when asked to extend.

**How they fail:** they signal arrogance without realizing it. The grader's question isn't "can you code?" — it's "would I want to be stuck debugging with you at 2am?" Arrogance is a 2am-debug liability. The committee picks against it.

**What wins instead:** play the game. Write the tests. Name the trade-offs. Even if you know the optimal answer, build the boring version first and name the upgrade path. Humility in the interview is a feature, not a weakness.

### Pattern 4: The "I have one great story and I tell it 5 times" candidate

You have one project from 2019 that you're proud of, and you stretch it across every behavioral question. Symptom: every answer is "at [X], I built [same thing]."

**How they fail:** they look like a one-trick pony. The interviewer wonders what they did for the other 5 years.

**What wins instead:** 5 stories minimum, rotated to fit the question. Each story has a different shape: research contradicted hypothesis / I was wrong / disagreement with senior / I shipped under pressure / I mentored someone. If you can't tell 5 different stories, you don't have enough material.

### Pattern 5: The "I'm not here for the mission, I'm here for the comp" candidate

You give great technical answers but flunk the mission fit round. Symptom: "I just want to work on hard problems" / "I'm flexible on what team" / "OpenAI seemed like the next logical step." No specific bet, no specific test, no specific disagreement.

**How they fail:** they fail the veto. Mission fit can override technical signal. The committee looks for "would I want this person on my team" — and "no specific reason to be here" reads as mercenary.

**What wins instead:** name a current OpenAI bet, disagree with part of it, propose a test. "I'd want to test whether deliberative alignment generalizes beyond the training distribution, or whether it just memorizes the safety policy. I'd run this on TruthfulQA-Hard with held-out safety categories." That wins.

### Coding round failure modes

1. **LeetCode-optimizing.** You jump to the cleverest data structure instead of the obvious one with a named trade-off. Symptom: you finish the code in 15 min, the interviewer has 30 min of dead air, and you didn't write a single test. Fix: pick the *boring* structure first, then say "I could use X here, but I'm picking Y because Z." Tests come second, not last.

2. **Defending every choice.** The interviewer asks "why not a hash map?" and you spend 3 min explaining why your approach is right. Symptom: you never say "fair point, here's the trade-off." Fix: every design question gets a trade-off answer, not a defense. "Hash map would be O(1) lookup but uses 2× memory; I picked sorted array for cache locality" wins. "Hash maps have collisions" loses.

3. **Skipping extensions because you "ran out of time."** You spent 40 min on the base spec. Symptom: when the interviewer adds a feature, you copy-paste instead of refactoring. Fix: budget 15 min for the base, 5 min for each extension, 5 min buffer. If you're at 25 min and not done, you're done — write what you have, name what's missing.

4. **Forgetting to think out loud.** The grader is watching process. Symptom: silent typing for 5 min, then "here's my solution." Fix: 30 seconds of "here's my approach" before any code. Then 5-second "now I'm doing X because Y" updates every line or two.

### System design failure modes

1. **Sketching the whole system before picking a layer.** You draw 12 boxes in 10 min and have no depth anywhere. Symptom: the interviewer asks "how does the queue work" and you have to think. Fix: name 3 layers, pick one to deep-dive, get specific. The candidate who goes deep on 1 layer beats the one who's shallow on 5.

2. **Naming trade-offs without numbers.** "We'd use Redis for caching" is a choice, not a trade-off. Symptom: no number ever appears. Fix: every trade-off has a threshold with a number. "Switch from local cache to Redis at >10K req/sec per instance" wins. "Use Redis for performance" loses.

3. **Designing for 1M users when the problem is 1K.** You over-engineer. Symptom: you mention Kafka, sharding, and a custom protocol for a 100-req/sec system. Fix: state the scale first. "This system serves 1K req/sec today, expected to grow to 100K in 12 months" — and then your design follows from that.

4. **Forgetting the cost attribution.** In a multi-tenant design, you forget who pays. Symptom: no per-tenant metrics, no token counting, no reconciliation. Fix: cost attribution is a first-class concern, not an afterthought. State where it lives (gateway middleware), what gets measured (per-request token count), and how it reconciles (nightly Stripe sync).

### Project walkthrough failure modes

1. **Describing the project, not what you did.** Symptom: "the team built a RAG system that…" Fix: "I built" / "I designed" / "I led." The interview is testing your contribution, not the team's.

2. **No number on the result.** Symptom: "it worked well" / "it improved performance." Fix: "it improved HotpotQA EM by 4% over the no-reranker baseline" / "it cut p99 from 800ms to 180ms." Every result has a number.

3. **No ablations you didn't run.** Symptom: you defend every choice when asked "what didn't you test." Fix: name 3, in priority order, with what you'd expect to find. The candidate who says "I didn't test OOD and that worries me" wins. The one who says "we tested everything" loses.

4. **Confusing contribution with proximity.** Symptom: you describe the team's work because you were on the team. Fix: if you didn't write the code or make the design decision, it's not your project. Pick one you actually owned.

### Behavioral round failure modes

1. **Generic STAR.** Symptom: 5 sentences of situation, 1 sentence of action, 1 sentence of result. Fix: situation is 1 sentence, action is 3 sentences, result has a number, lesson is 1 sentence. The whole story is 90 seconds, not 5 minutes.

2. **Result without a number.** Symptom: "it worked better." Fix: "it improved X by N%." Every result has a number, even if the number is approximate.

3. **No contradiction or failure.** Symptom: every story is a success. Fix: the interviewer is testing how you handle being wrong, how you handle conflicting evidence, how you update. Pick stories where you were wrong, where the data surprised you, where you changed your mind.

4. **Forgetting the lesson.** Symptom: the story ends with "and then it worked." Fix: every story ends with "what I learned" or "what I do differently now." The lesson is the part that shows belief updating.

### Mission fit failure modes

1. **"I want AGI."** Symptom: no specific bet, no specific test, no specific disagreement. Fix: name a current OpenAI bet, disagree with part of it, propose a test. The test is the point — it shows you can think.

2. **"I'm passionate about AI safety."** Symptom: values statement with no evidence. Fix: state the bet (deliberative alignment vs. RLHF), state the test (does it generalize beyond the training distribution), state the evidence you'd accept (yes if eval shows X, no if it shows Y).

3. **"OpenAI is the best place for me."** Symptom: comparison shopping language. Fix: state what OpenAI specifically does that you can't do elsewhere. "The cost-curve bet is bigger here than anywhere else" wins. "OpenAI has the best researchers" loses.

4. **Disagreeing without a test.** Symptom: "I disagree with X" but no "I'd test it by Y." Fix: every disagreement has a test. The test is the whole point.

## What failed candidates said they did wrong

Real reports from 2025-2026 candidates who were rejected. These are not abstract failure modes — these are the specific things people said in the post-loop thread.

### 1. They solved the shape but missed a buried invariant

Multiple 2026 phone-screen rejections describe the same pattern: the candidate recognized the problem class, picked a reasonable data structure, and got most of the tests passing — but missed a single re-ordering rule buried in the prompt. One candidate wrote:

> *"When a task is put back in the queue, it has to be ordered by its original enqueue time. I missed this one, so the unit tests did not all pass, and that ended in tragedy. Each task comes with a cooldown after it gets preempted, and you have to use the preempt timestamp to work out yourself when the cooldown ends."*
> — PracHub, OpenAI phone-screen rejection, Oct 2026

**The pattern:** LeetCode-prepped candidates optimize for the recognizable shape of the problem and miss the specifics. The OpenAI coding round hides its real test inside a constraint that looks like detail. **The fix:** read the prompt twice. List every invariant, every ordering rule, every cooldown. Write a test for each one *before* you code.

### 2. They over-narrated the project deep-dive

Several r/OfferEngineering threads from 2026 describe candidates steamrolling 8 minutes of project monologue, then getting cut off on follow-ups they should have anticipated. The pattern: candidates present the "hero founder" version of a project instead of the specific *technical decision with two real alternatives*.

**The pattern:** the project walkthrough is a 5-min slot, not a TED talk. **The fix:** 1 sentence on what you built, 1 sentence with the result, 2 min on the architecture, then stop and let the interviewer drive. They will ask the follow-ups — your job is to make those follow-ups easy to ask.

### 3. They over-engineered the system design on the first pass

One 2026 candidate wrote:

> *"Candidates who try to write the fully-extended version on the first pass consistently run out of time."*
> — Medium synthesis of OpenAI/Anthropic loops, Oct 2026

A second pattern: applying generic web architecture (REST + Postgres + a queue) to problems that need ChatGPT-specific design (multi-tenant chat backends, conversation state, content moderation, token-based billing). One candidate wrote:

> *"I struggled more with system design. One takeaway from that round was to clarify the requirements..."*
> — r/OfferEngineering, Aug 2026

**The pattern:** the failure is scope negotiation, not technical depth. **The fix:** state the scale first. State the 3 layers in 30 sec. Pick one to deep-dive. The interviewer will tell you which one they want to go deep on — listen for the hint.

### 4. They couldn't survive the behavioral follow-up

One synthesis: *"A weak values or behavioral round can override a strong technical round at both companies."* The failure mode: candidates give polished, rehearsed STAR stories but cannot answer a *follow-up* on a decision they made. Interviewers probe for the moment you changed your mind; candidates freeze because their story is too clean.

**The pattern:** rehearsed stories have no follow-up-able seams. **The fix:** every story should have one detail you didn't fully understand at the time, one moment you changed your mind, and one specific thing you'd do differently. If your story is too clean, the interviewer can't probe — and that itself is a signal of fabrication or naïveté.

### 5. They psych-ed themselves out of a real answer

A r/leetcode "self-sabotage" thread from 2025 describes a candidate who, mid-coding-round, abandoned the algorithm they had working because they read the interviewer's expression as cold. The candidate later learned the interviewer had rated them positively on the exact problem they abandoned.

**The pattern:** the loop is psychologically brutal. A flat expression isn't a rejection. A long pause isn't a sign you failed. **The fix:** commit to your answer. If you have a working solution in 25 min, do not throw it out to chase a cleverer one. The boring correct answer beats the abandoned clever one.

### 6. They treated the take-home like a portfolio piece

Multiple 2026 posts describe candidates spending the full 48 hours on the paid take-home polishing edge cases instead of writing the **3-paragraph design doc that the rubric actually scores on**.

**The pattern:** OpenAI evaluates the *judgment* of what you chose not to build, not the completeness of what you did. **The fix:** the design doc is the deliverable, not the code. Ship a working v1, write a tight design doc that names what you didn't build and why, and stop.

### 7. They prepared for the wrong interview

One 2026 candidate wrote:

> *"Prepared for the wrong interview... passing the rounds they prepared for and failing the rounds they did not."*
> — Medium, Oct 2026

**The pattern:** candidates over-prep the coding round (because it's the most concrete) and under-prep the project walkthrough and behavioral (because they think "I'll just talk about my work"). The HM round is the biggest single moment in the loop, and most candidates walk in with no practiced answer. **The fix:** spend 2 hours on the project walkthrough, not 2 hours on LeetCode.

### 8. They confused "AGI passion" with mission fit

Candidates report two opposite failure modes: (a) **generic AGI-safety monologue** with no specific tie to their own work, or (b) **narrow product obsession** ("I love ChatGPT's UX") that signals they haven't engaged with the research side.

**The pattern:** "I want to work on AGI" and "I want to work at OpenAI" both fail because neither names a falsifiable bet. **The fix:** name a current bet (deliberative alignment, cost-curve, Codex, the GPT-6 series), disagree with part of it, propose a test.

## Pre-mortem: "If you fail, which question killed you?"

Imagine you finished the loop and got rejected. Walk through, in order, which round was the most likely culprit and what specifically went wrong.

**Probability-weighted guesses (these are illustrative, not measured):**

| Round | Probability of being the killer | Most common failure |
|-------|-------------------------------|---------------------|
| Recruiter screen | 10% | Inflated level or title; no specific reason for OpenAI |
| HM round (project deep-dive) | 30% | No number on the result; can't name 3 ablations |
| Coding round (small system) | 35% | LeetCode-optimized, no tests, no extensions handled |
| System design | 15% | Sketched 12 boxes, no depth, no numbers |
| Behavioral | 5% | Generic STAR, no lessons, no numbers |
| Committee veto | 5% | Coherence gap between rounds (e.g., "systems" coding + "research" project) |

**The 5 questions that have killed the most candidates:**

1. **"Walk me through your most significant project."** Killed because: no number on the result, no ablations, "the team did it" instead of "I did it." If you only have one answer prepared in your entire loop, this is the one.

2. **"Why OpenAI, specifically?"** Killed because: "I want to work on AGI" / no specific bet / no disagreement. The candidate who can't disagree can't understand.

3. **The coding round base spec.** Killed because: LeetCode-optimized (finished in 20 min, no tests) or skipped tests to "save time" (tests are part of the rubric, not optional). The candidate who writes no tests gets downleveled.

4. **"What didn't you test on your ML project?"** Killed because: defending every choice / "we tested it all" / no priority order. The committee is testing whether you know the limits of your own work.

5. **"Why this design over X alternative?"** Killed because: defensive ("X has these issues") instead of trade-off ("X is faster but uses 2× memory; I picked Y because p99 was binding"). Defending sounds like overconfidence; trade-off sounds like judgment.

**If you fail, ask yourself these diagnostic questions:**

1. Did I get a calibration signal? (If yes, you probably weren't the level they wanted.)
2. Which round had the most awkward silence? (That's usually the killer.)
3. Did I write tests in the coding round? (If no, that's the killer.)
4. Could I name 3 ablations I didn't run? (If no, that's the killer.)
5. Did I name a number for every claim? (If no, that's the killer.)
6. Did the interviewer say "we'll get back to you in X days" or was it vague? (Vague = bad signal.)

## Calibration drills

5 problems at the right level of difficulty. If you can't solve them in the time limit, you're not ready. Time yourself.

### Drill 1: Token bucket (15 min)

**Problem:** Implement a token bucket rate limiter that supports per-key rate limits. Each key has its own rate and capacity. Include 3 tests.

**Pass criteria:**
- Working happy path in 5 min
- Tests written before the implementation, not after
- One named trade-off in your answer
- Lazy refill (no background thread)

If you can't pass in 15 min, your coding round will be painful.

### Drill 2: LRU cache (20 min)

**Problem:** Implement an LRU cache with O(1) get and put. Then extend to support TTL on each entry.

**Pass criteria:**
- Working LRU in 10 min (hint: ordered dict or doubly-linked list + hash map)
- TTL extension in 5 min
- 2 tests for the base, 2 tests for TTL
- One trade-off named (lazy eviction vs. background thread)

If you can't pass, the coding round's "extend 2-3 times" pattern will eat you alive.

### Drill 3: Mini in-memory DB with versioning (30 min)

**Problem:** Build a key-value store that supports `put(key, value)`, `get(key, version)` (return the value at that version), and `delete(key)`. Versions are monotonically increasing integers. New versions start at 1.

**Pass criteria:**
- Pick a data structure and say why in 1 sentence
- Working `put` and `get` in 15 min
- `delete` and version-snapshot `get` in 10 min
- 3 tests (basic put/get, get at version, delete doesn't affect old versions)
- One trade-off named (e.g., copy-on-write vs. in-place mutation + version log)

This is the closest analog to the directed-social-graph problem OpenAI is known for. If you can't pass, practice more.

### Drill 4: System design (45 min total: 5 min outline, 35 min deep dive, 5 min recap)

**Problem:** Design a multi-tenant LLM inference platform with cost attribution. 100 customers, peak 10K req/sec, p99 latency target 500ms.

**Pass criteria:**
- 3 layers named in 5 min (gateway, router, serving)
- Deep dive on ONE layer for 25 min (the gateway is the natural pick because of cost attribution)
- 3 numbers stated explicitly (p99, cost/1K tokens, throughput/GPU)
- 2 trade-offs named with thresholds
- Cost attribution strategy: where it lives, what it measures, how it reconciles

If you can't get to 3 numbers and 2 thresholds, you don't know system design well enough yet.

### Drill 5: Behavioral speed round (15 min for 3 stories)

**Problem:** Write down 3 behavioral stories, 90 sec each, on a single page. You must be able to deliver each one in 90 sec.

**Required stories:**
1. A time your research contradicted your hypothesis
2. A time you were wrong
3. A time you disagreed with a senior person and how you handled it

**Pass criteria:**
- Each story has a number on the result
- Each story has a lesson (what you learned / do differently)
- No story is generic — every detail is specific to you
- You can deliver each in 90 sec, timed

If you can't do this, you'll ramble in the behavioral round and lose.

## Decision tree for loop navigation

### Coding round decision tree

```
Start: read the problem
├── Is it a system I'd actually build on the job? (e.g., KV store, rate limiter, social graph)
│   ├── YES → Say "I'll pick a simple structure first, here it is"
│   └── NO  → Ask "is this a system you'd want me to build, or a pure algorithm?"
│
├── State data structure + complexity in 30 sec
│
├── Write 2-3 tests BEFORE code
│
├── Implement, thinking out loud
│
├── Extension 1 arrives
│   ├── Can I extend in place? → do it
│   └── Need refactor? → say "I'll refactor to X, takes 1 min"
│
├── Extension 2 arrives (similar)
│
├── Extension 3 arrives (usually the trickiest)
│   └── If you can't fit it: write the test, write a stub, say "I'd implement this with Y"
│
└── Recap in 30 sec: "Here's what I built, here's the 1 trade-off, here's what I'd test"
```

### System design decision tree

```
Start: read the prompt
├── State scale: req/sec, users, data volume
│
├── State 3 layers in 30 sec
│
├── Pick ONE layer to deep-dive (the one the prompt signals)
│
├── For 25 min, go deep on that layer:
│   ├── Component-by-component
│   ├── With numbers (p99, throughput, cost)
│   ├── With trade-offs (and the threshold for switching)
│   └── With failure modes (what breaks first)
│
├── Address the 2-3 likely follow-ups
│
└── Recap in 1 min: layers, the one I went deep on, 3 numbers, 2 trade-offs
```

### Project walkthrough decision tree

```
Start: pick the project
├── 1 sentence: what I built
├── 1 sentence: the result (with a number)
├── 2 minutes: how it works (system architecture, key choices)
│
├── Q: "What didn't you test?" (this WILL come)
│   └── 3 ablations, in priority order, with what I'd expect
│
├── Q: "What would you do differently?"
│   └── 1 specific thing, not "I'd do it better"
│
├── Q: "What was the hardest part?"
│   └── Specific, technical, with a number or constraint
│
└── Q: "Why this design over X alternative?"
    └── Trade-off, with the threshold where I'd switch
```

## Loop day logistics

**The night before:**
- Sleep 8 hours. Non-negotiable. Pulling an all-nighter to "study" loses you 5 IQ points.
- Eat a real dinner, not just coffee.
- Lay out clothes, snacks, water bottle, laptop charger.
- Skim the failure modes and the pre-mortem. Do not read new material.

**Morning of:**
- Wake up 3 hours before the loop starts. Eat protein. Hydrate.
- 30 min of skimming this doc (the loop-day checklist section).
- No new material. Trust the prep.
- Get to the location 15 min early (in-person) or test your setup 30 min before (remote).

**Between rounds:**
- 5-10 min break. Walk. Get water. Don't look at your phone.
- 1 min reset: "what's the next round's frame?" (small system / system design / project / behavioral)
- Don't review the round you just finished. You can't change it.

**Lunch break (if in-person):**
- Eat real food, not sugar. You'll crash.
- 15 min walk outside.
- Light skim of the next round's frame.

**If you have a round that went badly:**
- Don't spiral. One bad round doesn't kill you unless you let the next one suffer.
- Reset physically: water, walk, breath.
- Reset mentally: name the next round's frame out loud.

**The last 30 min of the day:**
- Behavioral. Save energy for this.
- If you're exhausted, say so. The interviewer will adjust. Don't fake energy.

**After the loop:**
- Send a thank-you to the recruiter. Keep it 2 sentences.
- Do NOT ask "how did it go" — they can't tell you, and asking signals anxiety.
- Take notes while it's fresh: which question surprised you, what would you do differently, what did the interviewer hint at.

## Counter-offer playbook (after the offer)

**The 48-hour window:**
- OpenAI gives you a decision window. Don't accept in the first 24 hours, even if you want it.
- Use the first 24 hours to: (a) verify the level with the recruiter, (b) check the comp band, (c) review the offer letter line-by-line.

**The level is the lever, not the number.** If the level is wrong, no number of dollars fixes it. Push back on level with: "Based on my scope at [X], I think L4 is the right level. Here's why: [2 specific scope claims]." Don't push back on level more than once.

**If you have a competing offer:**
- Disclose it to the recruiter. OpenAI will not match a competing offer unless the level matches.
- The negotiation lever: "I have an offer at [company] for [level] at $[number]. I prefer OpenAI but the level and comp need to match." Use this once, in writing, in the recruiter call.
- Do not bluff. Recruiters talk; your bluff becomes known in 6 months.

**If you don't have a competing offer:**
- You have no leverage. Don't fake it.
- The negotiation lever: ask for a one-time sign-on to bridge any gap to your current comp, framed as "I need to recover the unvested equity I'm leaving at [current company]." This is a real, defensible ask.

**The "what to ask" list before accepting:**
- Level (L3, L4, etc.) and the criteria used to set it
- Base, target bonus %, equity (RSUs, units, grant value, current FMV)
- Vesting schedule (4yr / 6mo cliff / 25% per year)
- Sign-on bonus, if any (and whether it's refundable if you leave in <12mo)
- Relocation package: temporary housing duration, moving cost cap, tax gross-up
- Immigration sponsorship: H-1B transfer, O-1, green card timing
- Start date flexibility
- Team and manager (do you know who you'd report to? If no, ask)
- The "first 90 days" expectations, in writing if possible

**The 2 things candidates miss:**
1. **Tax gross-up on relocation.** If OpenAI is relocating you, ask whether the relocation package is gross-up or taxable. A $50K relocation package becomes $35K after taxes if not grossed up.
2. **The first 90 days.** Ask the hiring manager: "What does success look like in the first 90 days?" If they can't answer, the team is understaffed or confused about your role. Either way, you want to know.

**If you need to decline:**
- 2 sentences. No need to explain. "Thank you for the offer. After careful consideration, I've decided to go a different direction. I appreciate the time the team spent with me."
- Don't burn the bridge. OpenAI hires in waves; you may re-apply in 18 months.

## If you only have 1 hour

Read these 5 sections, in this order:

1. **What the loop actually tests** (5 min) — the 5 things, in order of weight
2. **Level calibration** (5 min) — figure out your L-level
3. **T2.0: Project walkthrough template** (10 min) — fill in YOUR answer, not the model's
4. **T3.1.1: Directed social graph** (15 min) — code it, with tests, twice
5. **Tips for the OpenAI loop** (5 min) — the 9 bullets
6. **The 1 thing to remember** (1 min) — internalize it

Skip everything else. If you have 5 minutes more, do T1.2 (Why OpenAI). If you have 30 minutes more, do Drill 1 (token bucket).

---

## See also

- [Anthropic](./02-anthropic.md) — the other frontier lab; same model-serving focus, separate safety round
- [xAI](./04-xai.md) — Grok; smaller team, "speed" round replaces OpenAI's committee
- [DeepMind](./03-deepmind.md) — same model-research lens, Google-style committee
- [OpenAI Research](./38-openai-research.md) — if you're targeting the research org specifically

## Sources

- [OpenAI Official Interview Guide](https://openai.com/interview-guide/)
- [Prepare.sh — OpenAI Interview Process (2026)](https://prepare.sh/articles/openai-interview-process-2026)
- [IGotAnOffer — OpenAI Coding Interview](https://igotanoffer.com/en/advice/openai-coding-interview)
- [Levels.fyi — OpenAI compensation](https://www.levels.fyi/companies/openai/salaries/software-engineer)
- [Levels.fyi — OpenAI L4 SWE](https://www.levels.fyi/companies/openai/salaries/software-engineer/levels/l4)
- [6figr — OpenAI SWE 2026](https://6figr.com/us/salary/openai--software-engineer)
- [Glassdoor — OpenAI Interview Questions (2026)](https://www.glassdoor.com/Interview/OpenAI-Interview-Questions-E2210885.htm)
- [r/OfferEngineering — OpenAI Senior SWE Interview (Aug 2026)](https://www.reddit.com/r/OfferEngineering/comments/1vj0uh8/openai_senior_swe_interview_aug_2026/)
- [r/OfferEngineering — OpenAI Senior SWE Phone Screen (Aug 2026)](https://www.reddit.com/r/OfferEngineering/comments/1vwfkyp/openai_senior_swe_phone_screen_august_2026/)
- [r/OfferEngineering — OpenAI Senior SWE Technical Screen (Sep 2026)](https://www.reddit.com/r/OfferEngineering/comments/1w8ai50/openai_senior_swe_technical_screen_sep_2026/)
- [r/OfferEngineering — OpenAI Senior SWE Interview (Oct 2026)](https://www.reddit.com/r/OfferEngineering/comments/1wzedra/openai_senior_software_engineer_interview_it_felt/)
- [r/BetterOffline — OpenAI ends 12-month vesting cliff (Dec 2025)](https://www.reddit.com/r/BetterOffline/comments/1pm5ltc/exclusive_openai_ends_vesting_cliff_for_new/)
- [Forbes — OpenAI for-profit PBC restructuring (Apr 2026)](https://www.forbes.com/sites/paulocarvao/2026/04/27/as-openai-shifts-to-for-profit-its-foundation-controls-130-billion-who-benefits/)
- [Leon Consulting — OpenAI interview response time (2026)](https://leonstaff.com/blogs/openai-interview-response-time/)
- [CalibreOS — LLM System Design Interview Guide (2026)](https://www.calibreos.com/blog/genai-llm-system-design-interview-guide)
- [OpenAI — Deliberative Alignment (2024)](https://openai.com/index/deliberative-alignment/)
- [OpenAI — DevDay 2026 Recap](https://openai.com/index/devday-2026-recap/)
- [OpenAI — Built to benefit everyone: our plan (Jun 2026)](https://openai.com/index/built-to-benefit-everyone-our-plan/)
- [Business Insider — Altman's three-part strategy at DevDay 2026](https://www.businessinsider.com/sam-altman-unveils-openai-three-part-strategy-devday-2026-9)
- [InfoQ — OpenAI DevDay 2026 Recap](https://www.infoq.com/news/2026/10/openai-devday-2026/)
- [HeroHunt — What OpenAI and Anthropic Pay Engineers (2026)](https://www.herohunt.ai/blog/what-openai-and-anthropic-pay-engineers-2026/)
- [TechCrunch — DOJ oversight of OpenAI green-card sponsorships (Aug 2026)](https://techcrunch.com/2026/08/05/trumps-doj-gains-oversight-of-openais-green-card-employee-sponsorships/)
- [DOJ — OpenAI settlement on US-worker discrimination (Aug 2026)](https://www.justice.gov/opa/pr/civil-rights-division-secures-settlement-openai-discriminating-against-us-workers)
- [AceRound — OpenAI AI Interview Policy (Sep 2026)](https://www.aceround.app/blog/openai-ai-interview-policy/)
- [Ophy AI — OpenAI Interview Guide 2026](https://ophyai.com/blog/company-guides/openai-interview-guide)
- [Rafailov et al. — Direct Preference Optimization (2023)](https://arxiv.org/abs/2305.18290)
- [Singhal et al. — Disentangling Length from Quality in DPO (ACL Findings 2024)](https://aclanthology.org/2024.findings-acl.297.pdf)
- [Park et al. — Length-Controlled DPO (2024)](https://arxiv.org/abs/2403.07359)
- [Frantar et al. — GPTQ (ICLR 2023)](https://arxiv.org/abs/2210.17323)
- [PracHub — OpenAI phone screen rejection: fault-tolerant queue + typing race (Oct 2026)](https://prachub.com/interview-experiences/openai-software-engineer-interview-experience-phone-screen-failed-on-a-fault-tolerant-queue-and-a-typing-race-design)
- [r/InterviewCoderHQ — OpenAI SWE loop breakdown](https://www.reddit.com/r/InterviewCoderHQ/comments/1rhfjpw/openai_swe_interview_experience_full_loop/)
- [Medium — What Anthropic and OpenAI actually ask (Oct 2026)](https://medium.com/@codegrey/what-anthropic-openai-actually-ask-in-coding-interviews-65536b029d33)
- [r/leetcode — Self-sabotage at OpenAI interview (Mar 2025)](https://www.reddit.com/r/leetcode/comments/1j8x3og/selfsabotage_at_openai_interview/)
- [r/OfferEngineering — OpenAI Senior SWE Interview (Sep 2026)](https://www.reddit.com/r/OfferEngineering/comments/1vstgty/openai_senior_software_engineer_interview/)

---

## The 1 thing to remember

At OpenAI, the coding round is a small system — build it like a real codebase, test at every step, name the trade-offs out loud, and the loop opens. Everything else is signaling.