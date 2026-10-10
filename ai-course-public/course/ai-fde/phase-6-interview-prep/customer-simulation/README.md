# Module 11 — Customer Simulation (the highest-signal round at AWS FDE, Anthropic, Sierra AI)

> **The customer simulation is the round that filters the most candidates.** AWS FDE has a dedicated 60-90 min customer scenario round (round 6 of 6); Anthropic's customer simulation is the highest-signal stage of the loop; Sierra AI's customer simulation follows the take-home demo and tests whether you can defend your agent under pressure. **Most engineers never prepare for it** — and that's why it filters more candidates than LeetCode, decomposition, or system design combined. **The signal: a candidate who can stay calm with a frustrated executive, scope live, push back without damaging the relationship, and know when to say no — that candidate can do the FDE job.**

---

## Why this module exists

The Phase 6 modules teach frameworks. The company-experiences reports show you what the round looks like at specific companies. **This module teaches the round itself — the customer simulation pattern.** The 12 questions + answers below are the prep material; the 5 scenarios are the practice arena; the 5 anti-patterns are the disqualifiers.

The thesis: **the customer simulation is the most-tested, least-prepared round in FDE interviews.** General prep gets you past the resume screen. Decomposition prep gets you past the Palantir loop. **Customer simulation prep gets you past the AWS / Anthropic / Sierra AI loop.**

---

## The 4 things every customer simulation tests

1. **Calm under pressure** — Do you escalate your own emotional state when the stakeholder escalates?
2. **No overpromising** — Do you agree to deadlines you can't hit? Do you promise cost/quality numbers you can't deliver?
3. **Trade-off explanation** — Can you explain "we can ship faster if we accept this trade-off, but here's the failure mode" in plain English?
4. **Knowing when to say no** — Do you have the conviction to walk away from a bad scope, or do you capitulate?

**The 5 things the simulation NEVER tests:**

- Your coding speed (you're not coding during the simulation)
- Your recall of API syntax (no API references needed)
- Your Kubernetes knowledge (no infra questions)
- Your ML theory (no "explain transformers" question)
- Your resume (the interviewer already has it)

**The signal:** the candidate who treats the simulation as a coding test fails. The candidate who treats it as a customer conversation wins.

---

## The 5 most common customer simulation scenarios

These 5 scenarios appear in at least 3 of the major FDE loops (AWS, Anthropic, Sierra AI, Palantir, LangChain). Practice each one out loud with a friend before your loop.

### Scenario 1: "The chatbot in two weeks"

**The setup:** the customer wants a customer-facing chatbot deployed in 2 weeks for a sales event. They have no data, no eval set, no integration with their CRM. They want it "yesterday."

**The wrong answer:** "Sure, we can do that. Let's get started." (This is the most common failure. The candidate commits to a deadline they can't hit.)

**The right answer:** "I'd push back. A 2-week build with no data + no eval set is a recipe for failure. The chatbot will hallucinate on edge cases, fail in front of customers, and damage your brand. Here's what I propose: a 2-week MVP with limited scope — FAQ-only, 20% of customer queries, with a 'talk to a human' handoff for the rest. A 6-week full build with eval set, production artifacts, and rollback. The trade-off: we ship a smaller, safer product in 2 weeks; the customer's success team sees value; the full build follows."

**The 3 follow-up objections (and the right responses):**

1. **"We can't afford to wait 6 weeks."** → "I understand. The MVP is designed to ship value in 2 weeks. The full build is a follow-on. If the MVP succeeds, the full build is funded."
2. **"Our competitor is launching in 3 weeks."** → "That's a real risk. The MVP gets you to market in 2 weeks; the competitor ships first; your MVP iterates faster. Better to ship an 80% product than to ship nothing."
3. **"What if the MVP fails?"** → "It won't fail because we're scoping it small enough to succeed. FAQ-only, 20% coverage, human handoff for the rest. The eval set will tell us if the 80% is good enough."

**The Phase 1-5 cross-reference:** this is the **scoping refusal** pattern. The PacificFreight drafter's "we said no to Mei's refund tool" decision (Phase 4 capstone engagement) is exactly this pattern: scope small, ship, iterate.

---

### Scenario 2: "The CISO who blocks deployment"

**The setup:** the customer wants to deploy your AI service. The CISO says "no data leaves the network." Your service requires calling an LLM API. The CISO is unmovable.

**The wrong answer:** "I'll just tell them it's fine." (This is the second most common failure. The candidate dismisses the security concern.)

**The right answer:** "I'd clarify the constraint. There's a spectrum of options: (1) provider API with Zero Data Retention (ZDR), no-training, SOC 2, region pinning — data transits the provider; (2) hyperscaler-hosted in the customer's cloud (Bedrock, Vertex AI, Microsoft Foundry) — requests stay in their compliance envelope, model vendor doesn't receive them; (3) self-hosted open weights in VPC/on-prem (vLLM serving Qwen/Llama/gpt-oss-class) — full control, quality gap, ops burden. The trade-offs: option 1 is fastest but the CISO may not accept it; option 3 is most secure but slowest and most expensive. I'd recommend option 2 as the middle ground: frontier-model quality, hyperscaler compliance envelope, no data leaves the customer's cloud. Embeddings and vector stores must stay inside the boundary too; observability must be self-hosted; FDE access over customer's VDI halves velocity."

**The 3 follow-up objections (and the right responses):**

1. **"We can't use a hyperscaler. Our cloud is on-prem."** → "Then option 3 — self-hosted open weights in your VPC. We can fine-tune a Qwen or Llama model on your data; quality is 90-95% of GPT-4o-mini; cost is lower at scale. The ops burden: you'll need a small ML platform team to maintain it."
2. **"What about prompt injection?"** → "Tool permissions must not exceed what reading context justifies. Every tool call goes through a deterministic policy: which user can call which tool, with what rate limit, with what cost ceiling. The LLM only decides what it wants; the policy code decides what it gets."
3. **"How do we know the model won't train on our data?"** → "Enterprise API agreements contractually exclude customer data by default. We can also enable ZDR + region pinning. For hyperscaler deployment, the model vendor doesn't receive your data at all. We can show you the SOC 2 + DPA + architecture diagram."

**The Phase 1-5 cross-reference:** this is the **rejection-vs-pivot** pattern. The PacificFreight Phase 3 in-process redaction + rate limiter are exactly the "deterministic policy code decides what the agent may do; the model only decides what it wants" pattern.

---

### Scenario 3: "The scope creep mid-engagement"

**The setup:** 3 weeks into a 6-week engagement, the customer says "we need to add 4 more features to the deliverable." The 4 features are: (1) a multi-tenant layer (wasn't in the original scope), (2) an SSO integration (was deferred), (3) a custom dashboard (was a stretch goal), (4) a Slack integration (was a "nice to have").

**The wrong answer:** "Sure, we can do all of that." (This is the third most common failure. The candidate silently absorbs the scope creep and over-commits.)

**The right answer:** "I'd hold the line. The 6-week engagement has a defined scope; the 4 features you're asking for would extend it to 10 weeks. Here's what I propose: (1) we ship the original scope in week 6 as planned; (2) we identify which of the 4 features is highest-value and most-aligned with the original scope; (3) we propose a 4-week extension for just that feature. The trade-off: we ship on time, and we add the highest-value feature. The other 3 features become a separate engagement. Better to ship a 100% of the original scope + a 1-of-4 extension than to ship 50% of the new scope."

**The 3 follow-up objections (and the right responses):**

1. **"We need all 4. Our CEO committed."** → "I understand the pressure. The CEO commitment is real, but the team can only ship 100% of the original scope + 1-of-4. If we try to ship all 4, we'll ship none. Let me propose: we ship the original scope, identify the 1-of-4 most aligned, and the other 3 become phase 2. We can have the phase 2 conversation in week 8."
2. **"We can't afford a phase 2. The budget is committed to this engagement."** → "Then let's prioritize within the 4. If we can only ship 1, which one is highest-value? I'd suggest the SSO integration because it's foundational — without it, the customer can't deploy."
3. **"What if we just stretch the team?"** → "Stretching the team is how we ship late and lose quality. The team is at capacity on the original scope. Stretching produces a 70% solution, not a 100% solution."

**The Phase 1-5 cross-reference:** this is the **scope-as-contract** pattern. The PacificFreight Phase 1 evaluation plan + the Phase 2 change-request process are exactly this pattern: the scope is the contract; deviations are renegotiated, not silently absorbed.

---

### Scenario 4: "The pilot that failed in front of the VP"

**The setup:** your service is in a 4-week pilot with the customer. Week 3, the customer runs a demo for their VP. The demo hallucinates on a critical question. The VP emails: "we need to discuss this. The pilot is at risk."

**The wrong answer:** "We can fix that. Let me investigate." (This is the fourth most common failure. The candidate goes defensive and over-promises a fix.)

**The right answer:** "I'd respond within 24 hours with: (1) acknowledgment of the failure, (2) root cause analysis, (3) a fix timeline with a rollback plan, (4) a prevention plan for future demos. The structure: 'The VP demo failed because [reason]. Here's what we learned: [lesson]. Here's the fix: [specifics]. Here's the timeline: [X days]. Here's the rollback: [if the fix doesn't ship in Y days, here's what we do].' The tone: accountable, specific, no overpromising."

**The 3 follow-up objections (and the right responses):**

1. **"The VP is upset. We need to send someone in person."** → "I can come in person. Let's schedule for this week. The agenda: (1) demo the fix + the new eval set, (2) walk the VP through the prevention plan, (3) confirm the pilot timeline. I'd rather come prepared than rush in."
2. **"We need 100% accuracy before we can ship to production."** → "100% accuracy isn't achievable with LLMs. What we can commit to: 95% accuracy on the eval set, with confidence-based routing (low-confidence answers route to a human), and an eval dashboard that surfaces regressions. We can reframe from accuracy to outcome: '95% accuracy on the eval set, with human-in-the-loop for the 5%, and a 50% reduction in customer escalation rates.'"
3. **"We need a different model. Yours is clearly not good enough."** → "The model is part of the issue. The bigger issue is the eval set didn't catch the failure mode. The fix: (1) expand the eval set to include the failing scenario, (2) add a regression test to the CI pipeline, (3) re-run the pilot for 2 more weeks with the new eval set. We should not change models until we have an eval set that catches the failure mode; otherwise we don't know if the new model is better."

**The Phase 1-5 cross-reference:** this is the **postmortem-as-public** pattern. The PacificFreight Phase 3 SEV-1 postmortem (the 10-min OpenAI outage that hallucinated 4 drafts) is exactly this pattern: incident response, root cause, fix, prevention, public postmortem.

---

### Scenario 5: "When is AI the wrong tool?"

**The setup:** the customer wants to deploy AI for a problem that AI can't solve well. Examples: (1) an order-status chatbot (a lookup problem, not a language problem), (2) a clinical decision support system with zero tolerance for errors, (3) a "predict deal closures" model from a quarterly CRM that everyone lies in.

**The wrong answer:** "We can build that for you." (This is the fifth most common failure. The candidate agrees to a doomed engagement.)

**The right answer:** "I'd say no. Not this, and here's what instead. (1) The order-status chatbot: that's an API + template, not an LLM. You'd save 6 months of build + maintenance by using a deterministic lookup. (2) The clinical decision support: there's no AI system with zero error tolerance and no human review possible. We can build a draft system with confidence thresholds + human review, but not a zero-error autonomous system. (3) The deal-closure prediction: the data is too sparse (quarterly, dishonest) and the outcome isn't language-shaped. We can build a structured-data dashboard, but not an LLM prediction. The conversation: never just say no — say 'not this, and here's what instead.' Redirect to adjacent AI-paying problem or to the prerequisite (instrumentation, data cleanup) as phase one. One honest no is worth three mediocre pilots."

**The 3 follow-up objections (and the right responses):**

1. **"Our CEO said AI is the strategy. We need to ship something."** → "I understand the pressure. Here's the path: (1) ship the deterministic solution for the order-status problem (2 weeks, not 6 months); (2) use that as the data-cleanup foundation for an AI rollout in 3 months; (3) by then, you'll have the data to support a higher-quality AI use case. The CEO gets a ship in 2 weeks + an AI roadmap in 3 months."
2. **"Our competitors are using AI for this."** → "What they're shipping may not be working. Most 'AI' pilots in deterministic-lookup problems are wrappers around APIs with a chatbot front-end. The technical debt is huge. If your competitor is shipping that, you can ship better by NOT shipping it."
3. **"What if we just ship the AI version and see?"** → "I'd push back. Shipping a known-bad solution is a brand risk + a customer-trust risk. If the eval set can't pass, don't ship. Better to ship the deterministic version now and the AI version later than to ship the AI version now and lose trust."

**The Phase 1-5 cross-reference:** this is the **walk-away-with-data** pattern. The PacificFreight Phase 4 capstone "we said no after 2 weeks" engagement is exactly this pattern: a legal-tech customer whose data wasn't RAG-ready; the FDE walked away with a data-readiness check as the deliverable.

---

## The 12 specific questions + answers (the FDE interview bank)

These are real FDE interview questions from the AI-Engineer-Interview-Questions GitHub, paraphrased and expanded with the FDE framing. Use these as the practice bank.

### Q1: "CEO mandate with no use case" (the first 2 weeks)

**The setup:** the CEO has committed to deploying AI. The team has no specific use case. You have 2 weeks to deliver a "directionally right" first slice.

**The 4-week answer (per the AI Engineer guide):**

- **Week 1:** discovery. Interview 5-8 operators with the "hour-by-hour" question: walk me through your day, where do you spend time, where do you hit friction. NOT "what could AI do" (that produces science fiction). Inventory data reality early: what data exists, in what format, with what quality, owned by whom.
- **Week 2:** build a thin vertical slice on real data. A clickable artifact by day 10, framed as "directionally right, not production."
- **The deliverable:** working slice, ranked 2-3 follow-on use cases with effort estimates, named data-access blockers with owners.

**The 3 failure modes:**

1. Inventing a use case to fit the technology (instead of mapping the technology to the operator's pain)
2. Building a horizontal platform (instead of a vertical slice)
3. Skipping the data audit (and discovering the data is not RAG-ready at week 3)

---

### Q2: "48 hours to exec demo"

**The setup:** the customer wants an exec demo in 48 hours. They've given you 50 sample docs and a "make it impressive" request.

**The 48-hour answer:**

- **Hour 1:** lock scope. One workflow, one "wow" moment, 5 minutes. Resist the urge to ship 5 workflows at 1 minute each.
- **Hour 2-8:** build. Priorities: curated subset of their data (50 good docs beat 50,000 messy), hardened happy path with scripted queries tested 20× each, citations/grounding, clean boring UI.
- **Cuts:** auth/SSO, evals, edge cases, scale, agentic write actions (read-only for demos).
- **Hour 24-48:** rehearse. Run the demo on the venue's network if possible. Pre-plan the failure script.

**The 3 failure modes:**

1. Shipping a broad-but-shallow demo (5 workflows at 1 minute each, no wow moment)
2. Skipping the citations (the VP will ask "where did this come from?" and you'll have nothing)
3. Not rehearsing (the demo breaks on stage because the venue's network blocks your API)

---

### Q3: "Hospital COO: ER wait times too long. Can AI fix this?"

**The setup:** a hospital COO asks for AI to reduce ER wait times.

**The 60-min answer:**

- **Clarify:** "wait time" is a pipeline: arrival → triage → bed → physician → tests → disposition. Ask where the data says time goes.
- **Decompose:** sort stages by AI-suitability. Language-heavy, judgment-light steps (discharge paperwork, triage-note summarization) win. Prediction problems (admission likelihood) need historical data and validation.
- **Rule out:** autonomous clinical decisions. Even with 99% accuracy, the failure mode is unacceptable.
- **Propose:** a wedge — discharge-summary drafting. Measurable, language-native, human-reviewed by design.

**The 3 failure modes:**

1. Building the prediction (admission likelihood) — the data doesn't support it
2. Pitching autonomous decisions — the failure mode is unacceptable
3. Skipping the data audit — the discharge notes are scanned PDFs from 1998, no OCR

---

### Q4: "Pilot RAG wrong on contracts, on-site tomorrow"

**The setup:** your pilot RAG is wrong on 10% of contract queries. The customer is on-site tomorrow. You have 18 hours.

**The 18-hour answer:**

- **Hour 1:** ask for 10 concrete bad Q&A pairs from the customer.
- **Hour 2-4:** bisect per example: retrieval or generation? Pull the retrieved chunks and check whether the answer is present. Retrieval loses more often.
- **Signature causes for retrieval:** chunking severing clauses from defined terms; mangled tables/numbering; query rewriting for vocabulary mismatch; version confusion (metadata filtering, not better embeddings).
- **Signature causes for generation:** tighter grounding, per-chunk citations, force "not found" as valid.
- **Hour 5-18:** leave a small eval set from the failures. Deploy the fix. Rehearse the on-site.

**The 3 failure modes:**

1. Fine-tuning the model (instead of fixing the retrieval)
2. Adding more data (instead of fixing the chunking)
3. Skipping the eval set (so you can't tell if you fixed it)

---

### Q5: "CISO: no data leaves the network" (the spectrum of options)

**The setup:** the CISO says "no data leaves the network." Your service requires calling an LLM API.

**The 3 options (from cheapest to most secure):**

1. **Provider API with ZDR, no-training, SOC 2, region pinning** — data transits the provider; expensive but fast.
2. **Hyperscaler-hosted in customer's cloud** (Bedrock, Vertex AI, Microsoft Foundry) — requests stay in their compliance envelope; model vendor doesn't receive them; frontier-quality preserved.
3. **Self-hosted open weights in VPC/on-prem** (vLLM serving Qwen/Llama/gpt-oss-class) — full control; quality gap (90-95% of frontier); ops burden.

**Embeddings and vector stores must stay inside the boundary too. Observability must be self-hosted. FDE access over customer's VDI halves velocity.**

**The 3 failure modes:**

1. Dismissing the CISO's concern ("it's fine, we have SOC 2")
2. Pitching option 1 when the customer needs option 3 (the CISO blocks it)
3. Skipping the embeddings/vector store check (the LLM is inside, but the embeddings leak)

---

### Q6: "Agent takes write actions in ERP"

**The setup:** the customer wants an agent that creates POs in their ERP. You're worried about hallucinated actions.

**The deterministic-policy answer:**

- **Rule one:** never let a probabilistic system take irreversible actions without a deterministic gate.
- **Staging:** read-only → draft → gated write → scoped autonomy.
- **Deterministic policy code decides what the agent may do** (dollar thresholds, vendor allowlists, rate limits); the model only decides what it wants.
- **Tool design:** idempotency keys, dry-run variants, full audit log.
- **Prompt-injection review:** tool permissions must not exceed what reading context justifies.

**The 3 failure modes:**

1. Letting the agent create POs without a human review (the first hallucination is a 6-figure mistake)
2. Skipping the audit log (you can't tell what the agent did)
3. Not testing prompt injection (the agent's "create PO" tool becomes an attack vector)

---

### Q7: "CISO: how do we know your model won't leak or train?"

**The setup:** the CISO asks "how do we know your model won't leak or train?"

**The two-separately answer:**

- **Training:** enterprise API agreements contractually exclude customer data by default. Point to specific DPA language. Stronger: ZDR, region pinning, hyperscaler deployment.
- **Leakage** is subtler:
  1. Cross-tenant leakage through the model — training exclusion prevents this
  2. Intra-org leakage via ignored document ACLs — retrieval must enforce per-user permissions at query time
  3. Leakage via app — prompt injection, logging tools, browser plugins
- **Offer artifacts, not reassurance:** SOC 2, DPA, architecture diagram, pen-test window.

**The 3 failure modes:**

1. Conflating training and leakage (the customer assumes you're conflating them)
2. Skipping the ACL check (the most common intra-org leakage vector)
3. Reassuring without artifacts (the CISO needs to see the SOC 2, not just hear "we have one")

---

### Q8: "VP expects 100% accuracy after flawless demo"

**The setup:** the demo went perfectly. The VP now expects 100% accuracy in production.

**The outcome-not-accuracy answer:**

- **Don't argue about the model.** Reframe from accuracy to outcome.
- **Get a baseline of the status quo:** "94% versus your team's current 88%, at one-tenth the turnaround."
- **Make error handling a feature:** confidence-based routing, citations, eval dashboard.
- **Fix the root cause:** deliberately show one graceful failure in every demo and narrate why that builds trust.

**The 3 failure modes:**

1. Promising 100% (and being caught the first time the model hallucinates)
2. Dismissing the VP's expectation (without acknowledging the trade-off)
3. Skipping the confidence-based routing (which is the actual fix)

---

### Q9: "No labelled data, no eval culture"

**The setup:** the customer has no eval set and no eval culture. They want to ship AI in 4 weeks.

**The manufacture-labels-in-order answer:**

1. **Golden set from experts in week one** — 50-100 real input/expected-output pairs from historical traffic, including known-hard cases and "cannot be determined."
2. **LLM-as-judge for scale,** calibrated against humans on ~50 hand-graded outputs before trusting. Uncalibrated numbers are theater.
3. **Production signals from day one:** thumbs up/down, edit distance, escalation rates, retention.
4. **Report by slice, not aggregate** — aggregate 91% hides the one category at 60%.

**The 3 failure modes:**

1. Using LLM-as-judge without calibration (the numbers are theater)
2. Reporting aggregate accuracy (hides the failing slices)
3. Skipping the "cannot be determined" class (the model will hallucinate rather than say "I don't know")

---

### Q10: "Pilot to 5,000 users"

**The setup:** your pilot is succeeding with 50 users. The customer wants to scale to 5,000 next quarter.

**The almost-everything-changes answer:**

- **Identity/access:** SSO + per-user document ACLs at retrieval time. This is the #1 missing piece in most pilots.
- **Ingestion becomes a pipeline:** incremental sync, deletion propagation, parsing failure alerts, versioning.
- **Reliability:** rate limits, fallback models, caching, model tiering (cheap for routing, frontier for generation); latency re-examined (streaming, tighter context budgets).
- **Observability:** tracing on every request, golden set as CI regression gate, drift monitoring.
- **Organizational:** support path that isn't "Slack the FDE," runbooks, customer-team training, explicit definition of done to avoid permanent free staff augmentation.

**The 3 failure modes:**

1. Treating the pilot → production as a config change (it's a re-architecture)
2. Skipping the per-user ACLs (your intra-org leakage vector blows up at scale)
3. Skipping the support path (you become the support team, which means you can't do the FDE work)

---

### Q11: "Documents are scanned PDFs, broken spreadsheets, old SharePoint"

**The setup:** the customer's data is a mess: scanned PDFs, broken spreadsheets, 3 versions of every SharePoint doc.

**The triage-first answer:**

- **Triage before pipeline work:** sample 50-100 docs across sources, bucket by type, get volume distribution.
- **Ship on the clean 20% first.** Don't boil the ocean.
- **Toolkit:**
  - OCR or vision-capable LLMs for scans (route by document value)
  - Spreadsheets should not be chunked as prose — extract as structured tables, serialise row-wise with headers repeated, or give the system a query tool
  - SharePoint problems are permissions sprawl and duplication — dedupe, prefer latest-version metadata
- **Quantify the scope change; let the customer choose.**

**The 3 failure modes:**

1. Trying to process 100% of the data (scope creep)
2. Chunking spreadsheets as prose (you lose the tabular structure)
3. Skipping the SharePoint permissions (the data is the permissions, not the docs)

---

### Q12: "When is AI the wrong tool?"

**The setup:** the customer wants AI for a problem that AI can't solve well.

**The not-this-and-here's-what-instead answer:**

- **Cases where AI is wrong:**
  - Lookup not language problem (order-status chatbot is an API + template)
  - Zero error tolerance with no human review possible
  - Data doesn't exist ("predict deal closures" from a quarterly, dishonest CRM)
  - Rules engine already solves it
- **Conversation:** never just say no — say "not this, and here's what instead." Redirect to adjacent AI-paying problem or to the prerequisite (instrumentation, data cleanup) as phase one.
- **One honest no is worth three mediocre pilots.**

**The 3 failure modes:**

1. Saying yes to a doomed engagement (you'll burn 4 weeks)
2. Saying no without a redirect (the customer feels rejected)
3. Skipping the prerequisite conversation (instrumentation + data cleanup are the real phase 1)

---

## The 5 customer-simulation anti-patterns (the disqualifiers)

These 5 anti-patterns are instant-fail signals in every customer simulation. Memorize them.

1. **"Sure, we can do that."** (The overcommitting failure — Scenario 1's wrong answer)
2. **"It's fine, we have SOC 2."** (The dismissing-CISO failure — Scenario 2's wrong answer)
3. **"We can stretch the team."** (The absorbing-scope-creep failure — Scenario 3's wrong answer)
4. **"Let me investigate and get back to you."** (The going-defensive failure — Scenario 4's wrong answer)
5. **"We can build that for you."** (The agreeing-to-doomed-engagement failure — Scenario 5's wrong answer)

**The pattern:** every anti-pattern is a moment where the candidate gives up their FDE judgment to please the customer. The simulation tests whether you have the conviction to keep your judgment.

**The right answer in every case:** acknowledge the customer's pressure, propose a scoped alternative, explain the trade-off, and commit to a specific timeline + rollback plan.

---

## The 5-question "what would the candidate do differently" recap

These are the 5 things the customer-simulation candidate should do differently, distilled from the 12 questions above:

1. **Scope before committing.** Never agree to a deadline without scoping the data + the eval set + the rollback path.
2. **Trade-off in plain English.** "We can ship faster if we accept this trade-off, but here's the failure mode" — said calmly, with no defensiveness.
3. **Acknowledge the failure, propose the fix.** When the pilot breaks, don't go defensive. The structure: acknowledge → root cause → fix → timeline → rollback.
4. **Manufacture the labels before shipping.** Eval set first, system second. 50-100 hand-labeled examples + LLM-as-judge for scale.
5. **Say "not this, and here's what instead."** When the use case is wrong, redirect to the adjacent AI-paying problem or to the prerequisite.

**The signal:** the candidate who can do all 5 in a 60-min simulation is signaling they can do the FDE job. The candidate who can do 3 of 5 is signaling they need coaching. The candidate who can do 1 of 5 is signaling they're not ready.

---

## The cross-reference: how this maps to the 6 FDE company loops

| Company | Customer-simulation round | Cross-reference |
|---|---|---|
| **AWS FDE** | Round 6 of 6, 60-90 min, 3 scenarios | `../company-experiences/aws-fde-customer-simulation.md` § 2 |
| **Anthropic** | Round 3 of 5, 45-60 min, 5 scenarios | `../company-experiences/anthropic-fde-customer-simulation.md` § 2 |
| **Sierra AI** | Round 4 of 5, 45-60 min, 3 scenarios | `../company-experiences/sierra-ai-agent-engineer.md` § 4 |
| **Palantir** | Embedded in the decomposition round (not standalone) | `../company-experiences/palantir-fde-decomposition.md` § 2 |
| **LangChain** | Embedded in the Slack channel (the meta-skill) | `../company-experiences/langchain-deployed-engineer.md` § 3 |
| **OpenAI** | Embedded in the take-home walkthrough + the onsite | `../company-experiences/openai-semantic-search.md` § 3 |

---

## The thesis

**The customer simulation is the most-tested, least-prepared round in FDE interviews.** The 5 scenarios above appear in at least 3 of the 6 major FDE loops. The 12 questions + answers above are the canonical prep bank. The 5 anti-patterns are the instant-fail signals.

**The candidate who can stay calm with a frustrated executive, scope live, push back without damaging the relationship, and know when to say no — that candidate can do the FDE job.** All other rounds test technical skill; this one tests customer judgment.

**General prep gets you past the resume screen. Customer-simulation prep gets you past the AWS / Anthropic / Sierra AI loop.**
