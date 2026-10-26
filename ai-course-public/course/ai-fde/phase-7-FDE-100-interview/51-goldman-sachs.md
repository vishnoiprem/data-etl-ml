# Goldman Sachs — Platforms / AI FDE

## Company Snapshot
- **HQ**: NYC
- **Team Size**: ~150–250
- **Comp**: $170K–$250K; TC $250K–$450K
- **What they deploy**: GS AI Platform deployment
- **Travel**: ~0–15%

## Interview Process
1. Recruiter
2. Coding (medium-hard)
3. Bank ML / systems design
4. Loop — coding, scenario, GS values

---

## ✅ SUCCESS STORIES

### Bank ML case
**Q:** *"How to deploy AI Platform to desk-aligned devs (strats)?"*
**A (winner):** *"AI Platform gateway with model catalog (Claude, internal models), audit logs, RBAC by line of business, dedicated token budgets. Documented SDK + REST. Pilot with 1 desk (Equity Research) for 6 weeks; expand based on usage + incident rate."*
**Why it worked:** Right controls, named the platform, realistic rollout.

---

## ❌ REJECTION STORIES
### Bank ML scenario
**Q:** *"Model gives inconsistent answers."*
**A (loser):** "Set temperature to 0."
**What they should have said:** *"Two parallel fixes: (1) temperature=0 + seed for reproducibility, (2) add a retrieval + grounded prompting stack so answers come from one source of truth. Measure variance on 100 queries."*

---

## 📚 Reading List
1. GS developer public materials
2. Goldman Sachs Engineering blog
3. r/MLOps
4. levels.fyi Goldman