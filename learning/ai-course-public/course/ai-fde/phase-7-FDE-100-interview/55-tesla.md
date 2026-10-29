# Tesla — Autopilot / Optimus Deployment

## Company Snapshot
- **HQ**: Austin, TX
- **Team Size**: ~50–100
- **Comp**: $180K–$260K; TC $350K–$600K
- **What they deploy**: Robotaxi / Optimus FDE
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium-hard C++/Python)
3. Robotics / autonomy design
4. Loop — coding, scenario, Tesla cultural

---

## ✅ SUCCESS STORIES

### Robotaxi scenario
**Q:** *"You deploy a robotaxi in a new city. First 30 days?"*
**A (winner):** *"Maps: collect 1M miles of shadow-driving, generate lane-graph. Models: domain-adapt vision model, fine-tune on city-specific signs/lights. Ops: customer onboarding, edge-case call routing. Safety: NHTSA reporting, fault tracking. Pilot: 100 vehicles, 1 month."*
**Why it worked:** Tesla-flavored (shadow driving, vision model, fine-tune).

---

## ❌ REJECTION STORIES
### Robotaxi scenario
**Q:** *"Customer reports phantom braking."*
**A (loser):** "Tune the planner."
**What they should have said:** *"Reproduce: collect 100 phantom-brake clips, label root-cause (perceived vehicle ahead? shadow on lane? sign? object?). Patch + regression test. Fleet-wide OTA."*

---

## 📚 Reading List
1. Tesla AI / autonomy blog (Day of AI)
2. CVPR / ICRA papers on AV
3. r/TeslaMotors
4. levels.fyi Tesla