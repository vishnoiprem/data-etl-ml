# Saronic — FDE (Autonomous Surface Vessels)

## Company Snapshot
- **HQ**: Austin, TX
- **Team Size**: ~30–60
- **Comp**: $150K–$200K; TC $230K–$380K
- **What they deploy**: Autonomous surface vessels for Navy (Spyglass, Cutlass)
- **Travel**: heavy; sea trials

## Interview Process
1. Recruiter (often ex-Navy)
2. Coding (medium + robotics/ML)
3. Maritime autonomy design
4. Loop — coding, maritime scenario, customer scenario (Navy)

---

## ✅ SUCCESS STORIES

### Maritime scenario
**Q:** *"Navy wants a 30-day deployment of autonomous vessels for ISR."*
**A (winner):** *"Pre-deployment: 4 weeks of integration testing in-port + at-sea with Navy crew. Deployment: 2 vessels on 30-day mission, mission planning via Spyglass C2, comms via Starlink + Iridium fallback. Refuel by boat-crew at week 2. Daily debrief + Navy watch officer. Lessons-learned at week 4."*
**Why it worked:** Saronic-native (Spyglass, Cutlass), realistic Navy deployment arc.

---

## ❌ REJECTION STORIES
### Maritime scenario
**Q:** *"Vessel lost comms in rough seas."*
**A (loser):** "Add a backup antenna."
**What they should have said:** *"Comms loss in maritime is routine. Vessel should hold station (auto-return to GPS point), continue ISR mission autonomously, log everything to local storage, push when comms returns. Add acoustic modem fallback for emergencies."*

---

## 📚 Reading List
1. Saronic blog
2. COLREGs (maritime rules of the road)
4. Navy unmanned systems roadmap
5. levels.fyi Saronic