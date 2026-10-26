# MosaicML (Databricks) — Custom-Model FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~30–60
- **Comp**: $180K–$240K; TC $300K–$500K
- **What they deploy**: Custom-model deployments for regulated industries
- **Travel**: 20–35%

## Interview Process
1. Recruiter
2. Coding (medium + Python ML)
3. Custom-model training design
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### Custom-model scenario
**Q:** *"Bank wants a domain-specific LLM trained on internal communications."*
**A (winner):** *"Continued pretraining on bank corpus with Mosaic's streaming + FSDP; deploy via Databricks Model Serving. Eval: 5,000 prompt suite, internal rubric. Pilot: 1 use case (summarization). Compliance: data lineage + audit. Rollback if quality drops."*
**Why it worked:** Right MosaicML/Databricks stack + compliance.

---

## ❌ REJECTION STORIES
### Custom-model scenario
**Q:** *"Fine-tune overfit."*
**A (loser):** "More data."
**What they should have said:** *"Smaller LoRA rank, regularization, more diverse data, held-out eval. Train on tasks not surface form. Use early stopping. Pissa-init."*

---

## 📚 Reading List
1. MosaicML blog (now Databricks)
2. Composer + FSDP docs
3. LoRA / DoRA papers
4. levels.fyi MosaicML