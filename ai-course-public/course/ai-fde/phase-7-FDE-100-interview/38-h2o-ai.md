# H2O.ai — FDE

## Company Snapshot
- **HQ**: Mountain View, CA
- **Team Size**: ~30–60
- **Comp**: $150K–$210K; TC $230K–$380K
- **What they deploy**: Open-source LLM / AutoML deployments (H2O LLM Studio, Driverless AI)
- **Travel**: 20–35%

## Interview Process
1. Recruiter
2. Coding (medium + Python)
3. ML platform design
4. Loop — coding, ML scenario

---

## ✅ SUCCESS STORIES

### ML platform case
**Q:** *"Bank wants H2O LLM Studio for document classification."*
**A (winner):** *"H2O LLM Studio fine-tune (LoRA or full FT on Llama-3 8B), train on labeled docs, evaluate on hold-out. Deploy via H2O Inference + KServe on customer's K8s. Drift monitoring. Bias/audit checks. Eval: precision/recall + human-reviewed F1. Pilot: 1 use case, 4 weeks. Compliance + regulator sign-off in week 8."*
**Why it worked:** H2O-native (LLM Studio, KServe), structured.

---

## ❌ REJECTION STORIES
### ML scenario
**Q:** *"Fine-tune isn't working."*
**A (loser):** "Try LoRA."
**What they should have said:** *"Diagnose. Is the loss converging? Is the data labeled correctly? Often it's a labeling + class imbalance issue. Start with a small held-out eval set; iterate on data before model."*

---

## 📚 Reading List
1. H2O.ai docs
2. H2O LLM Studio github
3. Driverless AI docs
4. levels.fyi H2O.ai