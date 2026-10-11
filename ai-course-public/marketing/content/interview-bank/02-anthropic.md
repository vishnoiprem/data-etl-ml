# 2. Anthropic

> **Hero image spec:** 1400×788 px. Mood: editorial-technical (Stripe Press meets MIT Tech Review). Composition: the company name + 1 signature visual from the company's domain (Constitutional AI safety harness). Color: company brand color as accent (warm clay/terracotta). Headline on image: "Anthropic / AI Engineer / 2026".

> **TL;DR:** Anthropic's loop is 6 stages and ~99% rejection — the signature round is the standalone safety round (separate interviewer, weighted like coding), where you must name a specific safety decision you made and the trade-off you accepted. The winning candidate defends a specific Constitutional AI bet, names the alternative, and explains the open problem in plain English.

```
Recruiter (60%) → Hiring manager (50%) → Skills (40%) → Final loop (30%) → Committee → Offer
                                                                       └── safety round ──┘
```

- **Role:** AI Engineer (Safety)
- **Tech stack:** Python, PyTorch, Constitutional AI, RLHF, CodeSignal, Rust (perf)
- **Comp band:** $700K-$1.6M+ total comp (senior SWE-staff+, PPU-heavy) | RSUs 4-year, 1-year cliff
- **Cumulative pass rate:** ~1%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Resume screen** | "Direct evidence of ability" beats credentials | 1-2 weeks | ~30% advance |
| 2. **Recruiter call** | Motivation, background, safety interest | 1-2 weeks | ~60% advance |
| 3. **Hiring manager** | Past projects, including failures | 1-2 weeks | ~50% advance |
| 4. **Skills assessment** | 90-min CodeSignal OR 2-hr CUDA take-home (perf track) | 2 weeks | ~40% advance |
| 5. **Final loop (5 rounds)** | Coding → system design → ML theory → behavioral → **safety round** | 2-3 weeks | ~30% advance |
| 6. **Offer** | No negotiation — initial offer is final | — | — |

The loop looks like every other frontier lab on paper, but the safety round is the real differentiator — and it's graded by a separate interviewer, not folded into behavioral. Most candidates under-prepare it.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an ML engineer with 6 years of production experience, last at [X] where I shipped a safety layer for a customer-facing LLM. The relevant project: I led the red-team eval suite for [Y] that caught 3 category-naming regressions pre-launch. I'm here because the Constitutional AI approach is the only one I'd defend in a 2026 alignment context.
**Tip:** Anthropic grades "direct evidence" — show shipped safety work, not credentials.

### Q1.2: "Why Anthropic, specifically?"
**Answer:** I believe Constitutional AI addresses the scalability bottleneck of RLHF, but I want to test whether it inherits the biases of the principles you choose. The alternative I'd want to test: hybrid RLHF + Constitutional with a debate layer for ambiguous cases.
**Tip:** A specific Constitutional AI bet + a specific test is the Anthropic meta-answer.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Build an in-memory database, then add transactions, indexing, persistence"
**Answer:** Multi-level build, 15-20 min per level:
```python
class DB:
    def __init__(self): self.tables = {}
    def create(self, name): self.tables[name] = {}
    def insert(self, t, k, v): self.tables[t][k] = v
    def get(self, t, k): return self.tables[t].get(k)
    def delete(self, t, k): del self.tables[t][k]
```
**Level 2 (transactions):** wrap mutations in `db.begin()` / `db.commit()` / `db.rollback()` with a snapshot dict. **Level 3 (index):** secondary index dict `[col][val] → row_ids`. **Level 4 (persistence):** write-ahead log to disk, replay on startup. JSON for human-readable, pickle for complex Python objects (the Anthropic follow-up question).
**Tip:** Time the levels. The candidate who runs out of time on level 3 loses.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding

### Q3.1.1: "LRU cache → make it persistent → handle concurrent access"
**Answer:** Use `OrderedDict`; on `get`, move to end; on `put` at capacity, popitem(last=False). Persistence: pickle to disk on every mutation OR write-ahead log. Concurrency: `threading.Lock` around the cache; per-shard locks for high concurrency.

### Q3.1.2: "Producer-consumer with bounded buffer, clean shutdown"
**Answer:** `queue.Queue(maxsize=N)` + poison-pill sentinel for shutdown. Producer stops on poison-pill; consumer drains remaining items, then exits.
**Tip:** The clean-shutdown signal is what separates the answer from the right answer.

### Round 3.2: System design

### Q3.2.1: "Design an API for an LLM with a Safety Layer"
**Answer:** Three components: (1) Constitutional AI evaluator that scores outputs against a principle rubric, (2) human review queue for outputs < 0.7 on the rubric, (3) nightly red-team eval suite. Safety mechanism: written principles + a judge model. Threshold: 0.7 confidence. Failure mode the threshold catches: subtle jailbreaks that pass the prompt filter but fail the principle check.
**Tip:** Anthropic system design is "strip away features" — go deep on 1, cut the rest by name.

### Q3.2.2: "Design a 1-on-1 chat system (no channels, no threads)"
**Answer:** SQL (CockroachDB) for messages with sequence numbers per conversation; Cassandra if scale > 1B messages. WebSocket scaling via consistent hashing on user_id. Offline delivery: durable per-user mailbox queue; on reconnect, replay from last seen sequence number.
**Tip:** Cut features by name and explain why.

### Round 3.3: ML deep-dive

### Q3.3.1: "What is Constitutional AI? Strongest argument against it?"
**Answer:** CAI replaces human harm labels with written principles the model critiques its own outputs against — cheaper and more scalable than RLHF. Strongest counter: they inherit the biases of the principles you write. The unsolved problem: how do you write principles that catch failure modes you didn't anticipate?

### Q3.3.2: "Optimize a model for inference latency"
**Answer:** Three options: (1) quantization (INT8, INT4 — 2-4× speedup, <1% quality loss at INT8), (2) distillation (smaller student, 2-3× speedup), (3) hardware acceleration (TensorRT-LLM, FlashAttention). Trade-off: INT4 saves memory but adds accuracy variance. Right pick: INT8 quantization + FlashAttention for the first pass.

### Round 3.4: Behavioral + Safety

### Q3.4.1: "Tell me about a time you made a safety-first decision at the cost of speed"
**Answer:** I noticed [specific failure mode] in a customer-facing LLM 2 weeks before launch. I could have shipped without the fix; I delayed 2 weeks, added [specific guardrail], and the post-mortem showed it would have caught [specific incident] 3 months later. The team was annoyed. I'd do it again, but communicate the trade-off earlier.
**Tip:** Specific decision + specific trade-off + specific lesson is the Anthropic safety meta-answer.

### Q3.4.2: "If your model behaved differently in eval than in deployment, what's your protocol?"
**Answer:** Stop deployment immediately. Verify with a held-out eval set the model hasn't seen. If confirmed, treat as a deployment incident: roll back, root-cause the eval gap (data shift, prompt injection, reward hacking), then add the eval case to the red-team suite.
**Tip:** The safety round is a separate interviewer, not a sub-question.

The phone screen is a coding warmup. The onsite is where the safety bet gets tested in the open — system design goes 2-3× deeper than OpenAI's, and your ML deep-dive needs to name the mechanism, the trade-off, and the open problem.

## Stage 4: Hiring committee

The committee weighs the safety round as heavily as coding. They look for: (1) a coherent safety narrative — can you name a specific decision you made and the trade-off you accepted, (2) "second-order effects" thinking — can you describe what your system could do wrong, (3) Constitutional AI literacy — can you explain the mechanism, the trade-off, and the open problem in plain English. Committee can downgrade you even if the safety round went well.

## Stage 5: Offer

Anthropic does not negotiate salary. "The initial offer is the final offer." PPU (Profit Participation Units) vest over 4 years; heavy equity weighting. The play: get the level right in the recruiter call. Asking for more money is a non-starter and costs you leverage on team match. Comp packages are PPU-heavy; cash component is modest.

## Tips for the Anthropic loop

- **Safety round is separate, not a sub-question.** Prepare it like any other round.
- **System design goes 2-3× deeper than OpenAI.** "Strip away features" is the prompt style.
- **Multi-level coding is the test.** Time the levels; 15-20 min per level.
- **No salary negotiation.** Get the level right up front.
- **Constitutional AI is a bet, not a destination.** Defend a specific bet + name an alternative.
- **CodeSignal is the standard.** Practice 90-min multi-part problems.
- **Perf track:** 8× speedup in 2 hours is the take-home bar; AI tools allowed.

## Real candidate report

> *"It's not about finding a clever one-line solution; it's about building a system that can evolve. On persistence level: JSON is human-readable but pickle can handle more complex Python objects."*
> — [Anqi Silvia, My 2025 Anthropic Software Engineer Interview Experience](https://medium.com/@anqi.silvia/my-2025-anthropic-software-engineer-interview-experience-9fc15cd81a99)

## Sources

- [Anthropic Constitutional AI paper](https://www.anthropic.com/index/claudes-constitution)
- [Jobright — Anthropic Technical Interview Questions: Complete Guide 2026](https://jobright.ai/blog/anthropic-technical-interview-questions-complete-guide-2026/)
- [Anqi Silvia — My 2025 Anthropic Interview Experience](https://medium.com/@anqi.silvia/my-2025-anthropic-software-engineer-interview-experience-9fc15cd81a99)
- [Anqi Silvia — I Collected 20 Real Anthropic Interview Questions](https://medium.com/@anqi.silvia/i-collected-20-real-anthropic-interview-questions-heres-what-you-actually-need-to-prepare-51e7caa9b2a9)
- [Levels.fyi — Anthropic compensation](https://www.levels.fyi/companies/anthropic/salaries)
- [Glassdoor — Anthropic Interview Questions (2026)](https://www.glassdoor.com/Interview/Anthropic-Interview-Questions-E8109027.htm)

---

## The 1 thing to remember

At Anthropic, the safety round is a separate interviewer — prepare a specific decision you made, the trade-off you accepted, and the second-order failure mode, or the committee downgrades you no matter how well the coding went.