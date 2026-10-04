# AI Adoption Question Prep — "Drive the adoption of advanced analytics, machine learning, Generative AI, and AI-powered decision-making where they create measurable business value"

> **Purpose:** Full preparation file for the AI adoption line on the role's responsibility list. Fifth in the series: `strategy-question-prep.md` · `platform-architecture-question-prep.md` · `governance-question-prep.md` · `partnerships-question-prep.md` · this file.

---

## The Question

- **Round:** Onsite 2 (Duke Nguyen, VP Engineering) or Onsite 3 (Rajesh Krishnan, SVP Engineering); can also surface in Onsite 1 with the technical panel as a system-design deep dive
- **Source:** Job posting, line 5 of "Your Responsibilities" (`README.md`)
- **Verbatim:** *"Drive the adoption of advanced analytics, machine learning, Generative AI, and AI-powered decision-making where they create measurable business value."*
- **Likely probes:**
  - "Where would GenAI add measurable value at Katalon?"
  - "How do you evaluate an LLM feature?"
  - "RAG gives wrong answers. How do you debug?"
  - "When is RAG unnecessary?"
  - "Build vs buy a vector DB?"
  - "How do you approach AI agents safely?"
  - "What is prompt injection and how do you defend?"
  - "A new model is 5% better offline but doubles latency and cost. Ship?"
  - "What is your AI north-star?"
  - "When should the system abstain?"

---

## Framework Used

- **Strategic:** **Value × Readiness × Risk** ranking for use cases
- **Adoption loop:** **Job → Eval → Candidate → Shadow → Canary → In-prod eval → Feedback → Retire/Expand**

🔵 **Hook: "Job-to-be-done first. Eval harness before model. Lighthouse before scaling."**

---

## 60–90 Second Spoken Answer (lead with this)

> Three things drive adoption: **start with the job-to-be-done, build the eval harness first, prove value in production — not in a slide**.
>
> I'd rank use cases on **value × data readiness × risk**, then pick two as pilots — never five. For Katalon, the highest-value hypotheses are: AI-assisted test authoring (NL → test steps), failure triage (cluster failures, propose root cause), flakiness prediction, test selection, and RAG support assistant.
>
> Each has a **measurable task outcome**, not vanity usage:
> - Test authoring → time to first working test + suggestion acceptance rate
> - Failure triage → median time to verified triage + expert-rated correctness
> - Flakiness → reduction in CI minutes at equal defect detection
> - Support deflection → tickets deflected with no CSAT drop
>
> Adoption requires **governance, not just capability**: tenant-filtered retrieval, prompt-injection defense, citations, abstention, schema-constrained output, kill switches, opt-in for customer data.
>
> **Batch before real-time. Eval set before model. Internal pilot before customer-facing.** The lighthouse has SLOs, an owner, a rollback plan, and a verified outcome — not "users like it."

⏱️ ~85 seconds.

---

## Value × Readiness × Risk Matrix

For every AI use case, score on three axes:

| Axis | Question |
|---|---|
| **Value** | What's the decision or outcome? Dollar value? Volume? |
| **Readiness** | Is the data there? Labeled? Governed? Tenant-scoped? |
| **Risk** | Customer-facing? Uses customer data? Automated decisions? Reversible? |

**Pick the top 2 as pilots. Never 5** — pilot fatigue kills adoption.

🔵 **Hook: "Pick two. Ship one. Then pick the next two."**

---

## Katalon AI Use-Case Hypotheses (ranked)

| Use case | Value | Readiness | Risk | North-star metric |
|---|---|---|---|---|
| **AI-assisted test authoring** (NL → test steps) | High | Med | Med | Time to first working test + acceptance rate |
| **AI failure triage** (cluster, root-cause) | High | High | Med | Median time to verified triage + correctness |
| **Flakiness prediction** | High | Med | Low | CI minutes saved at equal defect detection |
| **Test selection** (which tests for a change) | High | Med | Med | CI minutes saved, defect detection held |
| **Support deflection via RAG** | Med | Med | Med | Tickets deflected, no CSAT drop |
| **Internal text-to-SQL** on semantic layer | Med | High | Low | Analyst request volume / self-service rate |
| **Requirements coverage suggestion** | Med | Med | Low | Coverage gap reduction |
| **Recommendations in onboarding** | Med | Low | Med | Activation lift in 7-day window |

🔵 **Hook: "Rank by value × readiness × risk. Pick two."**

---

## The AI Adoption Loop (memorize this)

```
1. JOB-TO-BE-DONE
   Define the task, the user, the decision, the cost of being wrong
        │
        ▼
2. EVAL HARNESS
   Stratified, versioned golden set BEFORE any model choice
   Metrics: retrieval recall@k, MRR; generation faithfulness, citation, calibration
        │
        ▼
3. CANDIDATE SYSTEM
   Prompt + retrieval policy + model + safety config + post-validation
   Hybrid retrieval (BM25 + vector), tenant filter, schema-constrained output
        │
        ▼
4. SHADOW → CANARY → ROLLOUT
   Shadow against baseline; canary by tenant/project; rollback hooks ready
        │
        ▼
5. IN-PROD EVAL (acceptance, edit-distance, override, escalation, latency, cost)
   Online + offline checks; confidence calibration; drift detection
        │
        ▼
6. FEEDBACK LOOP
   Thumbs, corrections, abstentions → training data + eval set refresh
        │
        ▼
7. RETIRE / EXPAND
   Keep if verified value; expand scope; or stop cleanly
```

🔵 **Hook: "Job first. Eval first. Lighthouse first. Then scale."**

---

## "Measurable Business Value" — the Anti-Vanity Frame

Every AI use case needs a **task outcome metric**, not usage:

| ❌ Vanity | ✅ Task outcome |
|---|---|
| "Users accepted 80% of suggestions" | "Time to first working test decreased by 35%" |
| "10k RAG queries/day" | "Support tickets deflected +0% CSAT drop" |
| "Model accuracy 92%" | "False-positive rate <5% on tier-1 decisions" |
| "AI assisted X% of failures" | "Median verified triage time cited" |

🔵 **Hook: "Verified outcomes, not usage. A user can accept plausible but wrong output."**

---

## AI Platform Capabilities (what you build)

| Capability | Why | Concrete |
|---|---|---|
| **Eval harness** | Decide before shipping | Versioned golden set + LLM-as-judge calibrated against humans |
| **Hybrid retrieval** | Beats pure vector for codes/names/tenants | BM25 + dense + metadata filter + tenant scope |
| **Feature store** | Prevent training-serving skew | Online + offline parity, point-in-time correctness |
| **Tenant isolation** | Cross-tenant leakage = severity-1 | Filter at retrieval, not after top-k |
| **Citations + abstention** | Groundedness + safety | Always cite, abstain when confidence low |
| **Schema-constrained output** | Reliable action | JSON schema + validation against business rules |
| **Kill switches** | Per feature / tenant / provider | One-click rollback to baseline |
| **Audit trail** | Compliance + debugging | Model + prompt + retrieved IDs + safety actions |
| **Cost + latency budgets** | Economics matter | Per-tenant budgets, degrade gracefully |
| **Drift monitoring** | Catch regressions early | Input + label distribution + confidence calibration |

---

## Common Probes — Pre-Rehearsed Answers

### Q1: "Where would Generative AI add measurable value at Katalon?"

🟢 *"Hypotheses to validate with the product team, each with a metric. (1) AI-assisted test authoring — NL to test steps; metric is time to first working test + suggestion acceptance. (2) Failure triage — cluster test failures and propose root cause; metric is MTTR to verified triage. (3) Test-impact analysis — predict which tests to run for a code change; metric is CI minutes saved at equal defect detection. (4) Support deflection via RAG. (5) Internal text-to-SQL on the semantic layer. I'd rank by value × readiness × risk and run two as pilots."*

### Q2: "How do you evaluate an LLM feature?"

🟢 *"Three layers. Offline: golden dataset, retrieval metrics (recall@k, MRR), generation metrics (faithfulness, citation, relevance), LLM-as-judge validated against humans on a sample. Pre-release: red-team for safety, injection, PII leakage. Online: acceptance rate, edit-distance, escalation rate, latency, cost per request, A/B vs baseline. Treat the eval set as a living asset reviewed every release."*

### Q3: "RAG gives wrong answers. How do you debug?"

🟢 *"Separate retrieval from generation. Check if the right chunk was in the top-k — if not, it's retrieval (fix chunking, add hybrid search, tune embeddings, add metadata filters, add a reranker). If the right chunk was there and the answer was still wrong, it's generation (tighten prompt, reduce irrelevant context, add citation requirements, stronger model). Most failures are retrieval — look there first."*

### Q4: "When is RAG unnecessary?"

🟢 *"When the knowledge base is small enough to fit in context, when the task is precise logic over tables/numbers (use tool-calling instead), or when retrieval quality is unreliable and a smaller fine-tuned model would do better. RAG is the default for enterprise knowledge, not the only tool."*

### Q5: "Build vs buy a vector DB?"

🟢 *"Decision drivers: scale, filtering needs, ops burden, where source data + access controls already live. You don't need a separate one if Postgres+pgvector, your warehouse's vector features, or OpenSearch fit the scale. Pick a dedicated vector DB when you need very large scale, low latency, advanced filtering, or hybrid features beyond what your existing system supports."*

### Q6: "How do you approach AI agents safely?"

🟢 *"Start with narrow, reversible tasks. Give the agent least-privilege tools, cap steps and spend, require human approval before irreversible actions, log full traces, evaluate on realistic task suites before release. Treat tool outputs and retrieved text as untrusted input — that's where injection comes from."*

### Q7: "What is prompt injection and how do you defend?"

🟢 *"Malicious instructions hidden in untrusted content (logs, scripts, customer docs, support tickets). Mitigations: treat retrieved text as data, never as system instruction; separate system policy from customer context structurally; filter on authorized tenant/project *before* scoring; limit tools by tenant/role/action; redact secrets before submission; validate structured outputs; defend downstream renderers against generated HTML/script injection; kill switches."*

### Q8: "A new model is 5% better offline but doubles p95 latency and cost. Ship?"

🟢 *"Not by default. Compute the marginal business value of the 5% lift vs the doubled cost and p95. If the use case is interactive and the cost/latency breach kills the UX, no. If the use case is batch, low-volume, high-value (e.g. failure triage) — yes, with canary. Always measure online (updated impact) before promoting. Optimise for verified task outcome, not offline metric."*

### Q9: "How do you detect model or prompt drift?"

🟢 *"Three layers. Input distribution drift (PSI, KS test) — has the user base shifted? Output distribution drift (label/feedback changes) — are suggestions being accepted less? Confidence calibration — is the model's stated confidence still matching actual accuracy? Slice regressions on critical segments (tenants, languages, frameworks). Alert on the trend, not just the threshold."*

### Q10: "What is your AI north-star metric?"

🟢 *"For failure analysis: verified reduction in time from failure to correct triage, subject to correctness, safety, reliability, cost guardrails. Usage and thumbs-up are diagnostic signals, not the ultimate value measure. The economic metric beats the engagement metric."*

### Q11: "A customer demands deletion of data that contributed to a model. What do you do?"

🟢 *"Document the policy with Legal first. If the customer's data was used in training (with their opt-in), document whether technical removal is possible — for many models, it's not. If it's not, the customer contract + product policy need to define what happens. Either way, the lineage + consent records are the evidence. Don't bluff — say what you can and can't do, then offer alternatives (delete from retrieval index, exclude from future re-trains)."*

### Q12: "What retrieval metrics can improve while answer quality falls?"

🟢 *"Easy — recall@k goes up because you returned more chunks, but the answer quality drops because the model gets distracted. Mitigation: cap top-k, rerank aggressively, compress retrieved context, or improve chunking. Always pair retrieval metrics with groundedness / citation-correctness on a small golden set."*

### Q13: "When should the system abstain?"

🟢 *"When confidence is below an empirically-set threshold, when tenant policy forbids the retrieval, when safety filters trigger, when the user role isn't authorized, when the input is ambiguous, or when there's no supporting evidence. Better an honest 'I don't know' than a confident hallucination. Track abstention quality — too many = underuse, too few = overconfident."*

### Q14: "What is the difference between model monitoring and product-outcome monitoring?"

🟢 *"Model monitoring = drift, calibration, latency, errors at the model level. Product-outcome monitoring = does the user accept it, does it reduce their time-to-decision, does the business metric move. Both are needed; product-outcome is the ultimate one. You can have a great model with no business impact, and a sloppy model that ships real value."*

---

## AI Governance (NIST AI RMF)

| Function | What it means at Katalon |
|---|---|
| **Govern** | AI inventory, model cards, owner per use case, intake for new AI |
| **Map** | Data lineage, customer-data opt-in, risk tier per use case |
| **Measure** | Eval harness, red-team, calibration, drift, cost/latency |
| **Manage** | Rollback plans, kill switches, incident process, periodic re-evaluation |

Aligned to **NIST AI RMF** so the language is shared with enterprise procurement teams.

🔵 **Hook: "Govern. Map. Measure. Manage. Same vocabulary as our enterprise buyers."**

---

## EU AI Act Tiers (name-drop if asked)

| Tier | Examples at Katalon |
|---|---|
| **Unacceptable** | None — never build these |
| **High** | AI that makes automated decisions affecting customers (credit, employment) |
| **Limited** | Customer-facing chatbots, content generation — transparency duties |
| **Minimal** | Internal code-review AI, internal text-to-SQL |

🔵 **Hook: "We're mostly Limited + Minimal. Transparency (when AI is involved) is the recurring duty."**

---

## Common Traps (red-flag answers)

- ❌ "Let's spin up a vector DB and a chatbot" — no eval harness, no value metric
- ❌ "Accuracy is 92%" without baseline — what was it before?
- ❌ "We'll add governance later" — without it, customer data leaks into training
- ❌ "Users like it" — that's engagement, not task outcome
- ❌ "RAG solves hallucination" — RAG reduces, doesn't remove; still need eval + abstention
- ❌ "Fine-tune the model" as a first move — usually RAG + better prompts win first
- ❌ "We'll use customer data to train" without explicit opt-in + lineage proof

---

## Practice Log

| Date | Time | Mode | Self-score (1–4) | Notes |
|---|---|---|---|---|
| | | (cold / timed / peer) | | |
| | | | | |

---

## Linked Material

- **Main prep doc:** `Katalon_Head_of_Data_Interview_Prep.md` Sections 9, 10, 15–17
- **Sister files:**
  - `strategy-question-prep.md`
  - `platform-architecture-question-prep.md`
  - `governance-question-prep.md`
  - `partnerships-question-prep.md`
  - `example-question-prep.md` (template)
- **Stories bank:** Section 21 — find S4 (AI prototype → production) and S5 (cross-functional)
- **Flashcards:** Section 23
- **Scoring rubric:** Section 20

---

## Checklist Before Walking In

- [ ] 90-second answer said aloud, no notes
- [ ] Value × Readiness × Risk matrix drawn
- [ ] Top 2 Katalon pilots named with metrics
- [ ] Adoption loop (7 steps) said in 30 sec
- [ ] RAG-debugging answer (retrieval vs generation split)
- [ ] Prompt-injection defenses named (not just "be careful")
- [ ] NIST AI RMF functions (Govern/Map/Measure/Manage) said
- [ ] EU AI Act tiers named (briefly)
- [ ] Anti-vanity frame ready (verified outcome, not usage)
- [ ] One real AI story (S4) from your own career

---

## Closing Sentence (if asked "anything else?")

> Adoption is not "we built it." Adoption is **decisions made better because of it**, measured in dollars, hours, and trust. **Eval harness before model. Pilot before scale. Verified outcome before vanity metric.** The lighthouse wins the room; everything else follows.