# Physical Intelligence — Robotics Foundation-Model FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~20–40
- **Comp**: $200K–$270K; TC $400K–$700K
- **What they deploy**: Robotics foundation-model FDEs (π0)
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (medium + robotics)
3. Robotics foundation model design
4. Loop — coding, deployment scenario

---

## ✅ SUCCESS STORIES

### Robotics FM scenario
**Q:** *"Apply π0 to a new robot in 4 weeks."*
**A (winner):** *"Data collection: 1 week, teleop demonstrations of 30 tasks in target domain. Fine-tune π0 with LoRA on 5–10 demos per task. Sim-to-real with domain randomization. Eval: 50 trials per task. Deploy with safety overlay (limit force, speed). Iterate weekly."*
**Why it worked:** Robot foundation model flow (data → LoRA → sim-to-real → safety overlay).

---

## ❌ REJECTION STORIES
### Robotics FM scenario
**Q:** *"Model fails on novel objects."*
**A (loser):** "More training data."
**What they should have said:** *"Add few-shot prompting with structured object descriptions. Or fine-tune on examples of the novel objects. Evaluate on a held-out set of novel objects to measure generalization."*

---

## 📚 Reading List
1. Physical Intelligence blog + π0 paper
2. Diffusion policy papers
3. r/robotics
4. levels.fyi PI