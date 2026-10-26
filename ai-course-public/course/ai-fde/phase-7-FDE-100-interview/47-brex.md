# Brex — AI FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~30–60
- **Comp**: $170K–$220K; TC $280K–$430K
- **What they deploy**: AI spend / corporate-card FDE work
- **Travel**: 10–25%

## Interview Process
1. Recruiter
2. Coding (medium)
3. Fintech / ML system design
4. Loop — coding, customer scenario

---

## ✅ SUCCESS STORIES

### Spend AI scenario
**Q:** *"Customer wants Brex to categorize 1M transactions automatically."*
**A (winner):** *"Brex's transaction categorization pipeline (TxP), with rules + ML fallback. Custom categories per customer's chart of accounts. Eval: 95% precision on customer's labeled sample. Pilot: 100K txns, tune, then scale to 1M. Continuous eval to detect drift."*
**Why it worked:** Brex-native (TxP), concrete metrics.

---

## ❌ REJECTION STORIES
### Spend scenario
**Q:** *"Categorization is wrong on travel."*
**A (loser):** "Better rules."
**What they should have said:** *"Diagnose. Sample mislabeled travel. Often ambiguous merchant name → use both merchant + memo field. Add a human review queue for low-confidence. Active learning loop."*

---

## 📚 Reading List
1. Brex engineering blog
2. Active learning primer
3. r/fintech
4. levels.fyi Brex