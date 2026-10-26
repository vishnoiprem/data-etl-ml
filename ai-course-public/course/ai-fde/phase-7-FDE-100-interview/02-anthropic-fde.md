# Anthropic — Forward Deployed Engineer

## Company Snapshot
- **HQ**: San Francisco, CA
- **FDE Team Size**: ~300–500 FDEs
- **Comp**: L4 TC $665K; L5 up to $750K; L6 $1.2M+
- **What they deploy**: Claude into enterprise customers (legal, finance, healthcare, gov); safety consulting; agent builds
- **Travel**: 30–60%, often weekly fly-out

## Interview Process (~4–6 weeks)
1. Recruiter call (30 min)
2. Technical screen — coding (60 min, LeetCode-style + Claude API mini-task)
3. Technical screen — system design with AI focus
4. On-site loop (3–5 hours)
   - Coding 2
   - LLM-system-design ("design an enterprise RAG platform for Acme Corp")
   - Customer-scenario roleplay
   - Safety / values
   - Bar-raiser (often with research engineer)

---

## ✅ SUCCESS STORIES

### Round 1 — Recruiter
**Q:** "Why FDE at Anthropic specifically?"
**A (winner):** *"I've spent 4 years building customer-facing ML — most recently at [bank] deploying fraud models to 12 BUs. Two of those deployments struggled because the model wasn't right for the operating context. Anthropic's FDE role sits exactly at that interface: you shape how the model is used *as much as* how it's built. Combined with the safety focus, that's the version of this job I want for the next 5 years. I'm not going to grow into an FAANG PM — I want to keep building, on-site, where the leverage is highest."*
**Why it worked:** Grounded in past work, name-checked "model + context" insight, showed conviction (not shopping), explained why *Anthropic* and not just "frontier lab #4."

---

### Round 2 — Coding (LLM-API integrated)
**Q:** *"Implement a function that takes a list of customer-support tickets and groups them by 'likely root cause' using the Claude API. You have a working API key."*
**A (winner):**
```python
import anthropic
def group_tickets(tickets: list[str]) -> dict[str, list[str]]:
    client = anthropic.Anthropic()
    prompt = f"""Group these support tickets by likely root cause.
    Return JSON: {{ "<root_cause>": ["ticket1", ...] }}
    Tickets: {tickets[:50]}"""
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        response_format={"type": "json"},
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(msg.content[0].text)
```
Then on the call: *"In prod I'd add (1) structured-output enforcement via tool use, (2) chunking if tickets > 50 because of context window, (3) an eval harness with 50 labeled examples so we can regression-test prompt changes, (4) caching for repeat tickets."*
**Why it worked:** Working code, then *immediately* the production-grade thinking (chunking, eval, caching). That's exactly the FDE-level reasoning.

---

### Round 3 — System design (AI-first)
**Q:** *"Design an enterprise Claude deployment for a top-10 US law firm. 5,000 attorneys, 50M docs, 3 use cases (drafting, research, due diligence)."*
**A (winner):**
- **Architecture**: ingestion → doc classifier → per-practice-area index in Pinecone/Vertex Vector Search → Claude with tool-use to call Westlaw / internal DMS → audit log of every prompt/response (Sarbanes-Oxley compliance).
- **Key design choices**:
  1. Per-practice-area indices (M&A vs litigation need different retrieval signals).
  2. Privilege-aware retrieval — never feed privileged docs back to model in a way that could leak across matters.
  3. Human-in-loop mandatory for any *draft sent to client*; Claude proposes, attorney approves.
  4. Evals: 100-attorney blind A/B; legal accuracy, citation accuracy, leakage rate.
  5. Rollout: 1 practice group first, 30 attorneys, 4 weeks, then expand.
**Why it worked:** Concrete, depth-first, surface the legal-specific risks (privilege, citation, drafting accuracy). Showed the candidate can scope a deployment, not just chain prompts.

---

### Round 4 — Customer scenario
**Q:** *"The customer's CISO pushes back: 'we don't want our data leaving our VPC.' How do you respond?"*
**A (winner):** *"That's the right question. I'd (1) walk them through the data flow and where data is processed at inference, (2) share our SOC2 + ISO 27001 reports, (3) offer an on-prem deployment of Claude via AWS Bedrock or our GovCloud SKU, (4) propose a 30-day pilot on a non-sensitive corpus to build trust, (5) commit to a quarterly security review. If they still say no, I'd ask which specific risk is highest and design around it — sometimes a hybrid where indexing lives on-prem but the LLM call goes to our VPC is the answer."*
**Why it worked:** Acknowledged the concern as legitimate, offered specific mitigations, didn't capitulate, scoped a path forward.

---

## ❌ REJECTION STORIES

### Rejection #1 — Coding
**Q:** *"Implement streaming JSON parsing."*
**A (loser):** Wrote a 30-line recursive-descent parser from scratch, missed the edge case of escaped quotes inside nested arrays.
**Why it failed:** Didn't communicate, didn't ask clarifying questions, jumped to implementation, didn't talk through edge cases.
**What they should have said:** *"Before I write code — should I assume valid JSON or handle malformed? Should I worry about backpressure? What's the test runner interface?"* Talk through it; flag the edge cases; ship incrementally.

---

### Rejection #2 — LLM system design
**Q:** *"Design an AI tutoring system for K-12."*
**A (loser):** *"I'd fine-tune Claude on math textbooks and use RAG over the curriculum. Add a reward model to make it engaging. Ship it."*
**Why it failed:** No mention of student safety (age-appropriate content, COPPA), no teacher/parent loop, no measurement, didn't account for hallucination on math problems, ignored hardware (what runs offline in a Chromebook?).
**What they should have said:** Lead with the persona model (student/teacher/parent), then the safety layer, then the deployment constraints (Chromebooks, bandwidth), then the eval system (curriculum-aligned + human grader), then the rollout (1 district, 1 grade, 6 weeks).

---

### Rejection #3 — Customer scenario
**Q:** *"Customer says the model's answers are too vague."*
**A (loser):** *"I'd tell them to use a better prompt."*
**Why it failed:** Dismissive; didn't offer diagnosis, didn't offer a deployment-side fix (eval-driven prompt improvement, few-shot examples, fine-tuning).
**What they should have said:** *"Let's diagnose first — pull 50 examples of 'vague' answers and label what's actually wrong (too broad? missing facts? wrong audience?). 70% of the time this is a retrieval or context problem, not a model problem. We'd ship a fix in week 1 and a measured improvement in week 2."*

---

## 📚 Reading List
1. Anthropic engineering blog — *"Building effective agents"*
2. Anthropic docs — *"Prompt engineering library"* and *"Tool use guide"*
3. Boris Cherney (Anthropic) — talks/podcasts on deployment engineering
4. Sequoia AI + Anthropic podcasts on enterprise GenAI
5. r/ClaudeAI threads tagged "enterprise deployment"
6. levels.fyi Anthropic FDE interview reports
7. *"Anthropic's $665K FDE offer"* (Akshika, LinkedIn)
