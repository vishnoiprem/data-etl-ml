# Flatiron Health — Oncology Deployment

## Company Snapshot
- **HQ**: NYC
- **Team Size**: ~30–60
- **Comp**: $160K–$220K; TC $250K–$400K
- **What they deploy**: Oncology data platform deployments
- **Travel**: 15–30%

## Interview Process
1. Recruiter
2. Coding (medium + Python)
3. Healthcare data / ML design
4. Loop — coding, oncology scenario

---

## ✅ SUCCESS STORIES

### Oncology scenario
**Q:** *"Cancer center wants Flatiron to integrate with their EHR."*
**A (winner):** *"Flatiron OncoEMR + FHIR-based bidirectional sync. NLP pipeline for unstructured documents (pathology, radiology). Compliance: HIPAA + 21st Century Cures. Pilot: 1 cancer center, 8 weeks. Eval: data-completeness, clinician time saved."*
**Why it worked:** Right FHIR + healthcare-data integration.

---

## ❌ REJECTION STORIES
### Oncology scenario
**Q:** *"NLP mis-extracted stage."*
**A (loser):** "Train more."
**What they should have said:** *"Look at 100 mis-labels. Often: ambiguity in source (pathologist can't decide), document quality (illegible scans), or label schema mismatch. Add human-in-loop review queue + confidence threshold."*

---

## 📚 Reading List
1. Flatiron blog + publications
2. FHIR docs
3. NLP for healthcare papers
4. levels.fyi Flatiron