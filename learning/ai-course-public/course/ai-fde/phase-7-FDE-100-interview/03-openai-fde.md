# OpenAI — Forward Deployed Engineer (Go-To-Market Engineering)

## Company Snapshot
- **HQ**: San Francisco, CA
- **FDE Team Size**: ~400–600 FDEs
- **Comp**: Mid $230K base, Sr $290K, Staff $330K–$370K; TC $700K–$1.28M (L5–L6)
- **What they deploy**: GPT / Agents / Assistants API into Fortune 500
- **Travel**: 40–60%

## Interview Process
1. Recruiter call
2. Technical screen — coding (HackerRank + SQL + Python)
3. Technical screen — LLM system design
4. On-site (3–4 hours)
   - Coding (mid-hard LeetCode)
   - System design — AI deployment at scale
   - Customer scenario with GTM engineer hiring manager
   - Bar-raiser (often a research engineer)

---

## ✅ SUCCESS STORIES

### Round 2 — Coding
**Q:** *"Given 10M chat messages per day, design the function `def is_toxic(msg) -> bool` and make it fast."*
**A (winner):** Started with regex + curated lexicon. Then said *"At OpenAI scale this isn't a function, it's a model endpoint. I'd call `omni-moderation-latest` async, batch messages, and return a tri-state {ok, review, block}. The latency budget for the review queue is 5 sec, and I'd pipe returns into a Redis stream so a labeling job can re-train on misses."*
**Why it worked:** Started pragmatic, scaled up to the right answer (use the moderation endpoint), then talked about ops (queue, retraining). Showed OpenAI-flavored thinking.

---

### Round 3 — System design
**Q:** *"Design an OpenAI deployment for Klarna-style customer-service automation handling 100K tickets/day."*
**A (winner):**
- **Flow**: incoming ticket → intent classifier (small fine-tune) → router to specialized agents (refund / dispute / general) → tool calls to order DB / Stripe → response drafted → human approval for sensitive cases → send.
- **Critical pieces**:
  1. Evals first (golden set of 1,000 tickets, weekly regression).
  2. Cost monitoring per conversation (avg tokens → per-ticket cost).
  3. Fallback to human if model confidence < 0.7 or sentiment spikes.
  4. Compliance: every response logged for 7 years (financial services).
  5. Rollout: shadow mode for 2 weeks → 10% traffic → 50% → 100%.

**Why it worked:** Showed production discipline (evals, cost, fallback) plus GTM instincts (rollout sequence).

---

### Round 4 — Customer scenario
**Q:** *"Klarna's CTO says 'your model hallucinates refund policies.' Your move?"*
**A (winner):** *"Three things in parallel this week. (1) Pull 100 hallucinated examples, categorize (wrong amount? wrong eligibility? made-up clause?), root-cause which are retrieval misses vs which are pure generation errors. (2) Ship a tool-use fix: every refund answer must call our policy-retrieval function first. (3) Build a nightly eval harness so we catch regressions. The pattern is: most 'hallucinations' at enterprise are retrieval problems wearing a generation mask."*
**Why it worked:** Hypothesis-driven (categorize first), structured response (3 things in parallel), concrete technical fix (tool use + RAG), and process fix (eval harness). OpenAI interviewers reward this level of structured speculation.

---

## ❌ REJECTION STORIES

### Rejection #1 — Coding
**Q:** *"Implement a rate limiter."*
**A (loser):** Wrote a token-bucket but didn't discuss trade-offs, didn't ask about distributed vs single-machine.
**Why it failed:** Skipped the design conversation. OpenAI FDE loops are about *how you think*, not just whether the code passes.
**What they should have said:** Ask the clarifying question: *"Single instance or distributed? If distributed, do we want eventual consistency or strict global limits?"* Then propose Redis-with-Lua, justify it, mention leaky-bucket as alternative.

---

### Rejection #2 — System design
**Q:** *"Design a Coding Assistant (Cursor-style) for a bank."*
**A (loser):** *"Embed the codebase, RAG over functions, call the LLM with context."*
**Why it failed:** No security/audit story for a bank, no latency budget, no mention of test-running, no diff/UI plan, no rollout.
**What they should have said:** Add a security layer (no PII in prompts), a latency strategy (streaming + speculative start), a sandbox to run generated code, an IDE integration plan (Cursor fork or VS Code extension), a rollout plan (10 devs → 100 → 500).

---

### Rejection #3 — Customer scenario
**Q:** *"Customer says GPT-4 is too slow."*
**A (loser):** *"Switch to GPT-3.5."*
**Why it failed:** Didn't ask *which* calls were slow, didn't offer streaming, caching, batching, distillation.
**What they should have said:** *"Let's profile. Where in the response chain is the latency — input tokens, model time, post-processing? Often it's (a) we can cache repeated context, (b) we can switch to streaming + first-token time, (c) we can batch async calls. There may also be a smaller fine-tune that's 5× cheaper at parity."*

---

## 📚 Reading List
1. OpenAI Cookbook — production patterns
2. Lilian Weng — *"LLM-powered agents"*
3. Hamel Husain + Shreya Shankar — *"Eval-driven development for LLM apps"*
4. Harrison Chase (LangChain) — *"How enterprises ship GenAI"*
5. OpenAI customer case studies (Morgan Stanley, Klarna, etc.)
6. r/MachineLearning + Blind threads tagged "OpenAI FDE"
7. levels.fyi OpenAI GTM Engineering debriefs
