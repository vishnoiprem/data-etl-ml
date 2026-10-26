# Weights & Biases — FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~40–80
- **Comp**: $170K–$230K; TC $270K–$450K
- **What they deploy**: MLOps platform deployments (W&B Models, Sweeps, Weave, Tables)
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (medium + Python)
3. ML platform design
4. Loop — coding, customer scenario

---

## ✅ SUCCESS STORIES

### ML platform case
**Q:** *"Customer wants to standardize ML experiments across 8 teams."*
**A (winner):** *"W&B Workspace per team, a single Org-level Project for cross-team tracking, Sweeps for shared tuning, Registry for model versioning, Launch for training jobs on Kubernetes. Add governance: teams register to the platform via SSO; quotas enforced via Launch. Pilot with team 1 for 4 weeks, expand 1 team per sprint. Weave for LLM eval across teams."*
**Why it worked:** W&B-native primitives, structured rollout.

---

## ❌ REJECTION STORIES
### ML platform
**Q:** *"Customer wants to compare 200 experiments."*
**A (loser):** "Use a spreadsheet."
**What they should have said:** W&B Tables, parallel coords, scatter plots across hyperparams, Group By / Filter on runs. Show multiple experiments in one view.

---

## 📚 Reading List
1. W&B docs + Reports
2. W&B YouTube tutorials
3. r/mlops threads
4. levels.fyi W&B
