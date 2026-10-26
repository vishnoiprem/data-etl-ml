# Vannevar Labs — FDE (Defense Intel AI)

## Company Snapshot
- **HQ**: Mountain View, CA
- **Team Size**: ~30–60
- **Comp**: $150K–$200K; TC $230K–$380K
- **What they deploy**: Defense intel / OSINT AI FDEs (Decide for Cyber, Physical)
- **Travel**: moderate; clearance preferred

## Interview Process
1. Recruiter
2. Coding (medium + Python data eng)
3. OSINT / intel-pipeline design
4. Loop — coding, intel scenario, customer scenario

---

## ✅ SUCCESS STORIES

### OSINT pipeline
**Q:** *"An intel customer wants to detect foreign disinformation on social media."*
**A (winner):** *"Van-decide pipeline: ingest social media via approved feeds → entity resolution (people, orgs, hashtags) → narrative clustering (BERTopic on posts) → anomaly detection on engagement velocity → analyst dashboard with provenance + confidence. Track entity-network changes over time. Eval on analyst-validated historical narratives. Bias check + civilian-protection guardrails (no targeting of domestic speech)."*
**Why it worked:** Vannevar-native (decide pipeline), addressed provenance + bias.

---

## ❌ REJECTION STORIES
### Intel scenario
**Q:** *"Too many false positives."*
**A (loser):** "Tune thresholds."
**What they should have said:** *"Sample 100 false positives, categorize: actor confusion (mis-attribution)? topic drift? multilingual? Often it's entity-resolution at the front. Improve ER precision first; FP drops 3-5×."*

---

## 📚 Reading List
1. Vannevar blog
2. RAND papers on OSINT
3. NIST 800-53 (gov compliance)
4. levels.fyi Vannevar