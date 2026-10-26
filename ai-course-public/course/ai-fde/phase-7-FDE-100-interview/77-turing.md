# Turing — FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~30–60
- **Comp**: $130K–$180K; TC $160K–$280K
- **What they deploy**: LLM coding-agent deployment for enterprise
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium)
3. Code-agent / software-dev scenario
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### Code-agent scenario
**Q:** *"Customer wants AI to write unit tests for their codebase."*
**A (winner):** *"Turing's code agent on top of customer's repo, context-aware. Quality gate: must compile + must pass any pre-existing tests. Eval: 100 PRs measured for human review reduction. Pilot: 1 service, 4 weeks."*
**Why it worked:** Right code-agent deployment with eval gates.

---

## ❌ REJECTION STORIES
### Code-agent scenario
**Q:** *"Agent introduced bugs."*
**A (loser):** "More review."
**What they should have said:** *"Add pre-merge build + test gates; reject agent PRs that fail. Use smaller-scope PRs. Track defect rate over time. Pair agent with linter + type checks."*

---

## 📚 Reading List
1. Turing blog
2. Test-driven agent papers
3. r/MachineLearning coding-agents
4. levels.fyi Turing