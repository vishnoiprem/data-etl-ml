# Wayve — AV Foundation-Model FDE

## Company Snapshot
- **HQ**: London, UK
- **Team Size**: ~30–60
- **Comp**: £100K–£160K; TC £180K–£320K
- **What they deploy**: AV foundation-model FDEs (LINGO, GAIA)
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (medium)
3. AV foundation model design
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### AV scenario
**Q:** *"Customer (UK retailer fleet) wants Wayve in delivery vans."*
**A (winner):** *"Wayve's GAIA-1/2 foundation model, fine-tuned on UK road data, edge-deploy on Orin. Discovery: 1 week mapping routes + edge cases. Pilot: 5 vans, 1 region, 8 weeks. Compliance: UK Automated Vehicles Act + DVSA. Eval: miles-per-intervention, edge-case taxonomy."*
**Why it worked:** Right UK-specific regulatory + AV foundation model.

---

## ❌ REJECTION STORIES
### AV scenario
**Q:** *"Vehicle misses pedestrian."*
**A (loser):** "More training."
**What they should have said:** *"Reproduce. Add to edge-case taxonomy. Fine-tune on that scenario. Red-team with adversarial sims. Always have AEB (automatic emergency braking) as backup. Investigate perception → planner → controller for which stage failed."*

---

## 📚 Reading List
1. Wayve research blog
2. UK Automated Vehicles Act 2024
3. r/SelfDrivingCars
4. levels.fyi Wayve