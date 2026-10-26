# Anyscale (Ray) — FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~50–100
- **Comp**: $170K–$230K; TC $270K–$450K
- **What they deploy**: Distributed AI infra deployments (Ray on Anyscale / customer K8s)
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (medium + Python data engineering)
3. Distributed systems design
4. Loop — coding, Ray architecture, customer scenario

---

## ✅ SUCCESS STORIES

### Distributed systems
**Q:** *"Design a hyperparam search across 1,000 GPU jobs."*
**A (winner):** *"Ray Tune with HyperOpt/Optuna search, ASHA scheduler for early stopping. Drivers on head node, workers on GPU pool. Each trial an Actor; state in Ray object store. Logs to MLflow + TensorBoard. Auto-retry on transient failures, with checkpointing. Tune's ExperimentAnalysis gives you the Pareto front."*
**Why it worked:** Ray-native, named the schedulers, addressed fault tolerance.

---

## ❌ REJECTION STORIES
### Ray scenario
**Q:** *"Ray job is slow. Why?"*
**A (loser):** *"Add more nodes."*
**Why it failed:** Didn't diagnose.
**What they should have said:** *"Profile. Is it task overhead? Object-store serialization? Hot-spotting on a single Actor? Likely candidates: reduce task granularity, use plasma/faster transport, batch object gets, eliminate the head-node bottleneck."*

---

## 📚 Reading List
1. Ray docs + Anyscale blog
2. Ray Tune paper
3. PLASMA object store paper
4. r/MachineLearning + r/mlops
5. levels.fyi Anyscale
