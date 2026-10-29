# Harvey — FDE (Legal AI)

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~40–80
- **Comp**: $180K–$240K; TC $300K–$550K
- **What they deploy**: Legal-domain AI agent FDEs (Harvey for Law Firms)
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (medium + Python)
3. Legal AI design
4. Loop — coding, legal scenario, customer scenario (with lawyer)

---

## ✅ SUCCESS STORIES

### Legal scenario
**Q:** *"A magic-circle firm wants Harvey across all 8 practice areas."*
**A (winner):** *"Practice-area-tuned Assistants: M&A (due diligence checklist generation, contract review), Litigation (case-law retrieval, brief drafting), Employment (policy review), IP (patent claim charts). Each is a domain-tuned agent + retrieval over that practice area's corpus (filings, memos, templates). Strict privilege: matter-isolated retrieval, no cross-matter leak. Audit log every prompt. Pilot with Litigation in week 1, M&A in week 4, etc. Eval: 50 lawyer-rated answers per practice area."*
**Why it worked:** Harvey-native (Assistants, practice-area tuning), named privilege as a first-class concern.

---

## ❌ REJECTION STORIES
### Legal scenario
**Q:** *"Lawyer says Harvey got the citation wrong."*
**A (loser):** "Add more cases."
**What they should have said:** *"Citation errors are killshots in legal AI. Add strict citation enforcement (every case cited must be in the retrieval top-K, with a verified citation extraction). Add a 'citation verifier' module — string-match the citation back to the source doc. Lawyer reviews before any output leaves Harvey."*

---

## 📚 Reading List
1. Harvey blog + customer announcements
2. *"Legal AI ethics"* (Stanford CodeX papers)
3. r/LegalTech
4. levels.fyi Harvey