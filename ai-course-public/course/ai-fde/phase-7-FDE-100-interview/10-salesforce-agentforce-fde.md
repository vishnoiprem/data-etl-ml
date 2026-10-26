# Salesforce — Agentforce FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~500+ Agentforce FDEs (rapid 2025–26 buildout)
- **Comp**: Base $170K–$220K; TC $250K–$450K
- **What they deploy**: Agentforce + Data Cloud for enterprise
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (Salesforce-flavored Apex/LWC optional + algorithms)
3. Customer scenario (heavy)
4. Loop
   - Coding
   - Agentforce platform design
   - Customer scenario roleplay with GTM team
   - Bar-raiser

---

## ✅ SUCCESS STORIES

### Agentforce platform design
**Q:** *"A Fortune 500 retailer wants to deploy Agentforce to 5,000 service agents. Design the architecture."*
**A (winner):**
- **Data Cloud**: unify CRM, ERP, loyalty data, clickstream into a single customer profile.
- **Agentforce agents**: 3 — *case-deflection agent*, *case-summarization agent*, *next-best-action agent*. Each has its own prompt + tool use.
- **Guardrails**: every agent action requires human approval except in low-risk tier (FAQ responses).
- **Rollout**: agent assist mode (suggest-only) for first 4 weeks, then partial autonomy, then full in Q4.
- **Evals**: weekly regression on 1,000 historical tickets; track deflection rate + CSAT.
**Why it worked:** Salesforce-native terms (Data Cloud, Agentforce), explicit 3-agent topology, human-in-loop design, rollout sequence.

---

### Customer scenario
**Q:** *"The customer's CIO is worried Agentforce will leak competitive info via prompts. Your response?"*
**A (winner):** *"Two technical mitigations. (1) Einstein Trust Layer masks PII before the prompt leaves the org — competitors can't be in the prompt anyway because they aren't in the data. (2) Prompt Defense + toxicity classifier catches prompt injection. Plus a cultural fix: every agent's actions are auditable and replayable. I can ship a PoC on a non-sensitive corpus in 2 weeks, measure leakage, and you'll have data before any go-live."*
**Why it worked:** Named Salesforce's actual feature (Einstein Trust Layer), addressed the specific concern with measurement.

---

### Coding
**Q:** *"Implement a debounce with cancellation."*
**A (winner):** Used `asyncio.Event` for cancellation, discussed timing semantics (leading vs trailing), unit-tested with fake clock.
**Why it worked:** Concurrency safe, tested, semantically correct.

---

## ❌ REJECTION STORIES

### Agentforce design
**Q:** *"Build us an agent."*
**A (loser):** *"I'll write a Python agent with LangChain + OpenAI."*
**Why it failed:** Wrong platform. Salesforce wants Agentforce, not LangChain.
**What they should have said:** Salesforce wants you to use their platform — *Atlas Reasoning Engine*, *Agent Builder*, *Data Cloud*. Stay on-platform.

---

### Customer scenario
**Q:** *"Customer says Agentforce took the wrong action."*
**A (loser):** *"We'll roll back."*
**Why it failed:** No root-cause, no corrective action, no measurement.
**What they should have said:** *"Let's pull the trace, see what context the agent had, what reasoning it followed. Likely cause: ambiguous policy doc or insufficient data in Data Cloud. Fix: tighten the policy doc, mask or enrich the data, add regression test, ship monitor + alert."*

---

## 📚 Reading List
1. Salesforce docs — Agentforce, Data Cloud, Einstein Trust Layer
2. Salesforce Architects blog (good architecture patterns)
3. Trailhead — Agentforce specialist badges
4. Dreamforce 2024 keynote (Agentforce launch)
5. levels.fyi Salesforce FDE
6. r/salesforce threads tagged "Agentforce"
