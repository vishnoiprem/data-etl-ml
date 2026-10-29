# Waymo — Deployment / Partner Ops FDE

## Company Snapshot
- **HQ**: Mountain View, CA
- **Team Size**: ~50–100
- **Comp**: $190K–$260K; TC $350K–$550K
- **What they deploy**: Autonomous-driving deployment / partner ops
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium + C++/Python)
3. Robotics / autonomy design
4. Loop — coding, AV scenario

---

## ✅ SUCCESS STORIES

### AV scenario
**Q:** *"City X wants Waymo deployment. Your first 60 days?"*
**A (winner):** *"Discovery: regulatory landscape, partner fleet ops, road-data coverage, weather/edge cases. Mapping: HD map build/refresh, road-graph coverage. Ops: fleet maintenance partner integration, customer-service training. Compliance: NHTSA + state DMV. Pilot: 1 city zone, 50 vehicles, 4 weeks."*
**Why it worked:** Right AV-deployment arc: discovery → mapping → ops → compliance → pilot.

---

## ❌ REJECTION STORIES
### AV scenario
**Q:** *"Vehicle disengages too often."*
**A (loser):** "Update the model."
**What they should have said:** *"Categorize disengagements — sensor fault? map mismatch? planner conservative? Add a disengagement classifier; build per-cause rollup; address top 3 causes."*

---

## 📚 Reading List
1. Waymo research papers
2. NHTSA AV regs
3. r/SelfDrivingCars
4. levels.fyi Waymo