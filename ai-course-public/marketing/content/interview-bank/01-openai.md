# 1. OpenAI

> **Hero image spec:** 1400×788 px. Mood: editorial-technical (Stripe Press meets MIT Tech Review). Composition: the company name + 1 signature visual from the company's domain (transformer blocks for OpenAI). Color: company brand color as accent (teal-green). Headline on image: "OpenAI / AI Engineer / 2026".

> **TL;DR:** The OpenAI loop runs 5 stages and kills ~98% of candidates — the gate is the "small system" coding round where you build (not LeetCode) a directed social graph with snapshot queries, then extend it 3 times in 45 minutes. The candidate who wins treats coding like a real codebase (tests at every step, names trade-offs) and names the 3 ablations they didn't run on their ML project.

```
Recruiter (80%) → Hiring manager (50%) → Skills (40%) → Final loop (25%) → Committee (60%) → Offer
```

- **Role:** AI Engineer
- **Tech stack:** Python, PyTorch, CUDA, Triton, vLLM, CoderPad
- **Comp band:** $251K-$1.89M total comp (L2-L7 SWE) | RSUs 4-year, 1-year cliff
- **Cumulative pass rate:** ~1-2%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, comp, role fit | 1 week | ~80% advance |
| 2. **Hiring manager** | Project deep-dive, mutual fit | 1-2 weeks | ~50% advance |
| 3. **Skills assessment** | Pair-coding, take-home, or technical test | 2 weeks | ~40% advance |
| 4. **Final loop (4-6 hrs)** | Coding → system design → project talk → behavioral → optional agentic round | 1-2 days | ~25% advance |
| 5. **Decision + offer** | References checked; no negotiation, but level calibration matters | 1 week | — |

The loop is the same as every other frontier lab, but the weight is different. Let me explain what I mean.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm a senior ML engineer with 6 years in production ML — most recently shipping a multi-tenant LLM inference platform at [X] that served 50M requests/day. The relevant project for OpenAI is the RLHF pipeline I built at [Y]: we took a 7B base model through SFT, reward modeling, and PPO with 3 ablation rounds. I'm here because I want to work on inference efficiency at frontier scale — your cost-curve bet is what I want to test.
**Tip:** OpenAI downlevels aggressively; state your years of experience honestly, not your title.

### Q1.2: "Why OpenAI, specifically?"
**Answer:** I'm skeptical of the pure-RLHF alignment path — I'd want to test whether constitutional or debate methods close the gap on the evals I've seen. I deeply believe in the cost-curve story: if inference gets 10× cheaper, we unlock a category of products that don't exist yet. The first is where I'd want to be a skeptic; the second is where I'd want to be a builder.
**Tip:** Specific bet + specific test + specific disagreement beats "I want to work on AGI" every time.

## Stage 2: Technical phone screen (60 min)

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
        b["tokens"] = min(self.capacity, b["tokens"] + (now - b["ts"]) * self.rate)
        b["ts"] = now
        if b["tokens"] >= n:
            b["tokens"] -= n
            return True
        return False
```
For per-tenant extension: maintain hierarchical keys (`tenant:user`), check tenant bucket first, refill user bucket from tenant bucket. OpenAI's graders want "named trade-offs + named thresholds," not 200 lines of code.
**Tip:** Write the smallest correct version first, then extend. No tests = automatic downlevel.

The phone screen tells you whether you can code. The onsite tells you whether you can think. Here's where the difference shows up.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding

### Q3.1.1: "Build a directed social graph with snapshot/version queries"
**Answer:** The right structure is an adjacency list of immutable versions keyed by timestamp; a snapshot query reads the version tree at the requested moment. For mutations: append a new version, link to parent. For reads: binary search the version array. OpenAI extends this 3 times in 45 min — tests after every extension.
**Tip:** Treat it like a real codebase; tests at every step.

### Q3.1.2: "Implement DPO loss with ties"
**Answer:** DPO loss = -log σ(β log(π_θ(y_w)/π_ref(y_w)) - β log(π_θ(y_l)/π_ref(y_l))). Ties: treat as separate preferred/dispreferred pairs with weighted averaging; the loss is the same per-pair, summed.
**Tip:** Derivations on the whiteboard are graded on correctness, not memorization.

### Round 3.2: System design

### Q3.2.1: "Design a multi-tenant LLM inference platform with cost attribution"
**Answer:** Three layers: API gateway (auth, tenant resolution) → inference router (model selection, batching) → serving (vLLM/TensorRT-LLM). Cost attribution: token-counting middleware writes per-tenant metrics to Prometheus; nightly job reconciles against Stripe. Trade-off: per-request overhead vs. accuracy — sample 1/10 requests in detail, extrapolate.
**Tip:** OpenAI's system design round signals what they want up front. "Don't focus on the model" = focus on serving.

### Q3.2.2: "Design a webhook delivery system with at-least-once semantics"
**Answer:** Durable queue (Kafka/SQS) + per-tenant ordering key + exponential backoff with jitter + dead-letter after 5 retries. Receiver uses event ID for idempotency. The right pick over Kafka: Postgres LISTEN/NOTIFY if scale < 100K/sec.
**Tip:** Name the threshold where you'd switch systems.

### Round 3.3: ML deep-dive

### Q3.3.1: "Walk through your most significant project, ablations, and what you didn't test"
**Answer:** I built a retrieval-augmented generation pipeline that beat the SOTA by 4% on HotpotQA. Three ablations I didn't run: (1) the same model on out-of-distribution Wikipedia vs. arXiv, (2) with 10× less training data, (3) against a different baseline (ColBERT instead of DPR). I'd run (1) first.
**Tip:** Naming the 3 things you didn't test beats defending everything.

### Round 3.4: Behavioral

### Q3.4.1: "Tell me about a time your research contradicted your hypothesis"
**Answer:** I hypothesized that DPO would beat PPO on a 7B alignment task. Result: DPO won on reward-model score but lost on human eval because of verbosity. I added a length penalty to the reward model, retrained, and DPO won both.
**Tip:** Specific, time-boxed story. Generic STAR loses.

### Q3.4.2: "A time you were wrong"
**Answer:** I believed quantization below 4-bit was unusable. I was wrong — a paper from [lab] showed 3-bit with GPTQ matches 4-bit on most tasks. I now test at every bit-width before deciding.
**Tip:** Show belief updating, not failure.

## Stage 4: Hiring committee

The packet goes to a hiring committee of 5-8 OpenAI staff+ engineers who vote on "would I want this person on my team?" The committee looks for: (1) a coherent technical narrative across rounds, (2) specific mission-fit evidence, (3) a "level" consensus (L3 vs. L5 is the most-disputed call). The committee can downgrade you even if every interviewer said yes. Average wait: 5-7 days.

## Stage 5: Offer

OpenAI does not negotiate salary in the traditional sense — the offer reflects the calibrated level. The play: get the level right in the recruiter call. Stock vests 4 years, 25% per year. Relocation + immigration support is real; RSUs are 4-year with 1-year cliff for most roles. Sign-on is rare but exists for senior candidates with competing offers. The candidate who tries to negotiate base loses the rest.

## Tips for the OpenAI loop

- **Coding is a small system, not LeetCode.** Build it like a real codebase: tests, error handling, naming.
- **System design signals what they want.** "Don't focus on the model" = focus on serving, caching, cost.
- **"I don't know" is a feature.** Name the 3 things you don't know about your own work.
- **AI tools vary by round.** Use them where allowed, catch the tool's mistakes.
- **Mission fit is weighted.** Generic "I want AGI" answers lose; specific bets win.
- **Inflating experience downlevels you.** Be honest about years.
- **The recruiter calibrates.** Don't anchor to your current title.

## Real candidate report

> *"The coding question asked me to implement a directed social graph that supported real-time versioning with snapshot queries. It wasn't a LeetCode hard — it was a small system I'd actually have to build on the job. I extended it three times as the interviewer added requirements. Tests at every step."*
> — [r/OfferEngineering, OpenAI Senior SWE Interview (Aug 2026)](https://www.reddit.com/r/OfferEngineering/comments/1vdpjty/openai_senior_software_engineer_interview/)

## Sources

- [OpenAI Official Interview Guide](https://openai.com/interview-guide/)
- [Prepare.sh — OpenAI Interview Process (2026)](https://prepare.sh/articles/openai-interview-process-2026)
- [Levels.fyi — OpenAI compensation](https://www.levels.fyi/companies/openai/salaries/software-engineer)
- [Glassdoor — OpenAI Interview Questions (2026)](https://www.glassdoor.com/Interview/OpenAI-Interview-Questions-E2210885.htm)
- [r/OfferEngineering — OpenAI Senior SWE Interview (Oct 2026)](https://www.reddit.com/r/OfferEngineering/comments/1wzedra/openai_senior_software_engineer_interview_it_felt/)

---

## The 1 thing to remember

At OpenAI, the coding round is a small system — build it like a real codebase, test at every step, name the trade-offs, and the loop opens.