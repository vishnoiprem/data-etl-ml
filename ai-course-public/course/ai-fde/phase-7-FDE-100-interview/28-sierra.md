# Sierra — FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~30–60
- **Comp**: $180K–$240K; TC $300K–$500K
- **What they deploy**: Customer-experience AI agents
- **Travel**: 20–35%

## Interview Process
1. Recruiter
2. Coding (medium)
3. Agent platform design
4. Loop — coding, CX scenario, customer scenario

---

## ✅ SUCCESS STORIES

### CX scenario
**Q:** *"A telecom wants an agent that can handle plan changes and billing disputes."*
**A (winner):** *"Sierra Agent with two workflows — `plan_change` (tool calls into account API) and `billing_dispute` (tool calls into billing API + retrieval from policy docs). Composer for the agent's reasoning loop; customer-specific guardrails from CRM. Escalate to human when confident=false or sentiment<0.4. Eval on 500 historical cases with custom scoring rubric. Pilot for 1 month on 10% traffic."*
**Why it worked:** Sierra-native (Agent, Composer, workflows), explicit guardrails.

---

## ❌ REJECTION STORIES
### CX scenario
**Q:** *"Customer says the agent hallucinates policy details."*
**A (loser):** "Add more docs to RAG."
**What they should have said:** *"Categorize the hallucinations — wrong amount? wrong eligibility? pulled from wrong doc? Likely root-cause: retrieval misses ambiguous terms. Fix: re-rank + grounded prompt that quotes the doc. Add regression eval."*

---

## 📚 Reading List
1. Sierra blog
2. Sierra SXSW / conference talks
3. r/CustomerExperience
4. levels.fyi Sierra
