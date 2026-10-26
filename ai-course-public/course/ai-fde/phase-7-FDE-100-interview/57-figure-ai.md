# Figure AI — Humanoid Deployment

## Company Snapshot
- **HQ**: San Jose, CA
- **Team Size**: ~30–60
- **Comp**: $180K–$240K; TC $300K–$500K
- **What they deploy**: Humanoid robot deployment engineers
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (medium-hard + robotics)
3. Manipulation / humanoid system design
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### Humanoid scenario
**Q:** *"Customer wants a humanoid for warehouse picking."*
**A (winner):** *"Figure 02 with custom grippers + warehouse-specific skill library (pick tote, place, scan). On-site for 6 weeks: map routes, calibrate camera, train on customer's SKUs. Eval: picks/hour, error rate, human handoff rate. Pilot: 1 cell, 30 days. Compliance: OSHA + customer safety."*
**Why it worked:** Right humanoid-deployment arc.

---

## ❌ REJECTION STORIES
### Humanoid scenario
**Q:** *"Robot drops object."*
**A (loser):** "Better gripper."
**What they should have said:** *"Categorize: force-sensing failure? misperception? wrong grasp plan? Add force-feedback tuning, perception fallback (visual servoing), teleop handoff for low-confidence."*

---

## 📚 Reading List
1. Figure AI engineering blog
2. Manipulation papers (DEX-ART, etc.)
3. r/humanoidrobotics
4. levels.fyi Figure