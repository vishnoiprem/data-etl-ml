# Cerebras Systems — FDE

## Company Snapshot
- **HQ**: Sunnyvale, CA
- **Team Size**: ~30–60
- **Comp**: $170K–$230K; TC $280K–$460K
- **What they deploy**: CS-3 cluster / inference deployments
- **Travel**: 25–50%

## Interview Process
1. Recruiter
2. Coding (medium + numerical/ML)
3. ML infra design
4. Loop — coding, inference case, customer scenario

---

## ✅ SUCCESS STORIES

### Inference design
**Q:** *"Run a 100B-param model for a pharma customer needing HIPAA-grade inference."*
**A (winner):** *"Cerebras Cloud or on-prem appliance with dedicated cluster. Weight streaming + activation fabric means we can serve models larger than any single GPU's memory. HIPAA via BAA + on-prem deployment option. Use the Cerebras Inference API with batched + streaming; integrate with customer's VPC via PrivateLink."*
**Why it worked:** Knew Cerebras's actual SKUs (CS-3, weight streaming, on-prem), addressed HIPAA.

---

## ❌ REJECTION STORIES
### Pharma scenario
**Q:** *"Customer needs HIPAA inference."*
**A (loser):** "Just use the API."
**What they should have said:** BAA-required. On-prem Cerebras appliance option. Customer-managed keys. Audit logs.

---

## 📚 Reading List
1. Cerebras docs / inference blog
2. CS-3 architecture papers
3. levels.fyi Cerebras
