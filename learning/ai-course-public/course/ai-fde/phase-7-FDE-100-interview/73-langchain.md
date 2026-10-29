# LangChain — FDE (Enterprise LangGraph / LangSmith)

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~20–40
- **Comp**: $170K–$230K; TC $280K–$450K
- **What they deploy**: LangGraph / LangSmith enterprise
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium + Python)
3. Agent platform design
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### Agent case
**Q:** *"Customer wants a multi-agent workflow with LangGraph."*
**A (winner):** *"LangGraph stateful graph, persistent checkpointer, tool calls per node, supervisor pattern for coordination. LangSmith for tracing + evals. Eval: per-node graders + end-to-end. Deploy: LangGraph Cloud or self-host. Pilot: 1 workflow, 4 weeks."*
**Why it worked:** Right LangGraph/LangSmith framing.

---

## ❌ REJECTION STORIES
### Agent scenario
**Q:** *"Agent loops forever."*
**A (loser):** "Limit loops."
**What they should have said:** *"Add max_steps, recursion limits, tool-call budget. Detect loops (repeating state hash) and break. Inspect LangSmith traces for stuck state. Add a 'no-progress' guardrail."*

---

## 📚 Reading List
1. LangGraph docs
2. LangSmith docs
3. *"Agents"* — Harrison Chase talks
4. levels.fyi LangChain