# JPMorgan Chase — AI/ML Engineering (LLM Suite)

## Company Snapshot
- **HQ**: NYC
- **Team Size**: ~300+ AI/ML engineers
- **Comp**: $170K–$280K base; TC $190K–$420K
- **What they deploy**: LLM Suite / Index AI deployment (internal)
- **Travel**: ~0–15% (mostly on-prem)

## Interview Process
1. Recruiter
2. Coding (medium-hard)
3. ML + bank infra design
4. Loop — coding, ML scenario, finance/behavioural

---

## ✅ SUCCESS STORIES

### Bank ML scenario
**Q:** *"How would you deploy LLM Suite for 200K employees?"*
**A (winner):** *"JPM LLM Suite gateway with model-routing (Claude, Bedrock, internal models); RBAC + audit logs; SOC + FINRA compliance; cost-budget per desk. Pilot with 5,000 users in 1 line of business for 8 weeks. Measure usage + risks. Rollout in waves of 25K. Whitelisted use cases only (no fully autonomous)."*
**Why it worked:** Right bank controls (RBAC, audit, compliance), named LLM Suite.

---

## ❌ REJECTION STORIES
### Bank ML scenario
**Q:** *"Trader asked the LLM for stock picks."*
**A (loser):** "Block it."
**What they should have said:** *"Add a guardrail (no personalized investment advice) + audit + warning. Constraint + graceful refusal. Train the model with a 'forbidden-pattern' retraining."*

---

## 📚 Reading List
1. JPMorgan LLM Suite public materials
2. FINRA / OCC compliance for AI
3. r/MachineLearning "JPMorgan"
4. levels.fyi JPMorgan