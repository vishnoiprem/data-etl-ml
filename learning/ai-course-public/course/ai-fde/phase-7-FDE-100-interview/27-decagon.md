# Decagon — FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~40–80
- **Comp**: $170K–$230K; TC $280K–$500K
- **What they deploy**: AI agent platform for customer support
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (medium + Python)
3. Agent / LLM system design
4. Loop — coding, support-agent case, customer scenario

---

## ✅ SUCCESS STORIES

### Support-agent case
**Q:** *"A retailer wants AI to handle 80% of support tickets."*
**A (winner):** *"Decagon Agent + Actions layer (tool calls to OMS, returns, refunds). Knowledge sources from help center + past tickets. Policies enforced as code (can refund up to $X, else escalate). Escalation handoff with full context to human. Eval: 1,000 historical tickets scored by AI — deflection rate, escalation rate, CSAT. Deploy in 3 phases — shadow mode → 30% → 80%."*
**Why it worked:** Decagon-native (Agent + Actions), explicit policies, eval-driven.

---

## ❌ REJECTION STORIES
### Support scenario
**Q:** *"Customer says the agent is rude."*
**A (loser):** "Add politeness to the prompt."
**What they should have said:** *"Pull transcripts of 'rude' agent responses. Is it the tone? The wrong info? The wrong action? Often it's tone-of-voice mismatch + doing the wrong action (refusing things it could do). Iterate the prompt + the policies."*

---

## 📚 Reading List
1. Decagon blog
2. Anthropic Building Effective Agents
3. r/MachineLearning support-AI threads
4. levels.fyi Decagon
