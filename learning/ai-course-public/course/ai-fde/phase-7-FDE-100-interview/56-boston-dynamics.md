# Boston Dynamics — Deployment Engineer (Spot / Atlas)

## Company Snapshot
- **HQ**: Waltham, MA
- **Team Size**: ~30–60
- **Comp**: $170K–$230K; TC $280K–$450K
- **What they deploy**: Spot / Atlas deployment engineers
- **Travel**: 25–50%

## Interview Process
1. Recruiter
2. Coding (medium + robotics)
3. Robot system design
4. Loop — coding, scenario, customer case

---

## ✅ SUCCESS STORIES

### Spot scenario
**Q:** *"Customer wants Spot to do industrial inspections 24/7."*
**A (winner):** *"Spot + Spot CAM + Orbit fleet manager. Charging docks auto-positioned. Vision model for gauge reading + anomaly detection (compare to baseline). Alert pipeline to plant SCADA. Failure modes: lighting (add IR camera), battery (auto-dock at 30%), comms (4G failover). Pilot: 1 plant, 4 weeks."*
**Why it worked:** Boston Dynamics-native (Orbit, Spot CAM), failure-mode coverage.

---

## ❌ REJECTION STORIES
### Spot scenario
**Q:** *"Spot fell down stairs."*
**A (loser):** "Update the controller."
**What they should have said:** *"Categorize: slippery surface? step height > limit? misclassification of stairs? Add stair-classification model + better slip detection. Add a 'stair refusal' fallback to caller. Customer training: don't run on wet surfaces."*

---

## 📚 Reading List
1. Boston Dynamics docs (Orbit, Spot API)
2. Quadruped locomotion papers
3. r/robotics
4. levels.fyi Boston Dynamics