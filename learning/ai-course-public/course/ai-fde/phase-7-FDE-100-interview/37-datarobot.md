# DataRobot — FDE

## Company Snapshot
- **HQ**: Boston, MA
- **Team Size**: ~50–100
- **Comp**: $160K–$220K; TC $250K–$400K
- **What they deploy**: AI platform deployments (DataRobot AI Platform)
- **Travel**: 25–45%

## Interview Process
1. Recruiter
2. Coding (medium + Python)
3. ML platform design
4. Loop — coding, ML deployment scenario

---

## ✅ SUCCESS STORIES

### ML platform case
**Q:** *"Bank wants DataRobot for credit risk modeling with full governance."*
**A (winner):** *"DataRobot AI Platform with MLOps governance: model registry with sign-off workflow, feature store, drift monitoring, challenger/champion. Citizen users in Workbench; advanced in Notebooks. Compliance: full lineage from data → features → model → deployment. Pilot: 1 model in week 4. Expand to 5 in week 12. Validators: bias, stability, fairness."*
**Why it worked:** DataRobot-native (Workbench, Notebooks, governance), compliance-first.

---

## ❌ REJECTION STORIES
### ML platform scenario
**Q:** *"Customer wants to score in real time."*
**A (loser):** "Use the API."
**What they should have said:** *"Set up a DataRobot deployment as a REST endpoint with a feature store, pre-computed features for low-latency. Benchmark p95 latency; usually <50ms is achievable for tree models. For sub-10ms, export the model to ONNX and run in-process."*

---

## 📚 Reading List
1. DataRobot docs + customer stories
2. ONNX / model export patterns
3. r/MachineLearning
4. levels.fyi DataRobot