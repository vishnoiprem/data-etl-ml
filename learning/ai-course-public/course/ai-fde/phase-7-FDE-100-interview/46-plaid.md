# Plaid — Solutions / FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~30–60
- **Comp**: $180K–$230K; TC $300K–$450K
- **What they deploy**: Bank-link / fintech FDE work
- **Travel**: 15–30%

## Interview Process
1. Recruiter
2. Coding (medium + Python/JS)
3. Fintech API / integration design
4. Loop — coding, customer scenario

---

## ✅ SUCCESS STORIES

### Fintech integration
**Q:** *"Customer wants Plaid + their existing core banking."*
**A (winner):** *"Plaid Link for consumer auth, Auth endpoint for tokens, Identity / Balance / Income per use case. Webhooks for status updates. PCI: never store credentials. Sandbox → Development → Production with progressive perms. Eval: ACH conversion rate vs incumbent, time-to-first-deposit. SLA: 99.95%."*
**Why it worked:** Plaid-native (Link, Auth, Identity), progressive permissions.

---

## ❌ REJECTION STORIES
### Fintech scenario
**Q:** *"Customer sees dropped users."*
**A (loser):** "Make the flow faster."
**What they should have said:** *"Funnel diagnostic: where do users drop? Institution picker? Login? MFA? 60% of drops are at institution picker — show 'top 10 most-used' and search at top. Test with 20 users."*

---

## 📚 Reading List
1. Plaid docs (Link, Auth, Identity)
2. r/fintech
3. levels.fyi Plaid