# Robinhood — FDE

## Company Snapshot
- **HQ**: Menlo Park, CA
- **Team Size**: ~20–40
- **Comp**: $180K–$240K; TC $300K–$500K
- **What they deploy**: Brokerage AI / Cortex FDE
- **Travel**: 10–20%

## Interview Process
1. Recruiter
2. Coding (medium)
3. Trading system / ML design
4. Loop — coding, customer scenario

---

## ✅ SUCCESS STORIES

### Trading scenario
**Q:** *"Customer wants to integrate with Robinhood for retail brokerage."*
**A (winner):** *"Robinhood Connect for on-ramp; Robinhood Crypto API for trading; webhooks + KYC flow. Production keys gated on App Review. Audit logs. Compliance: SEC Reg ATS, FinCEN MSB."*
**Why it worked:** Robinhood-native (Connect, Crypto), compliance-aware.

---

## ❌ REJECTION STORIES
### Trading scenario
**Q:** *"Customer reports failed trades."*
**A (loser):* "Add retry."
**What they should have said:** *"Diagnose: API rate limit? slippage? insufficient funds? Most order failures are insufficient funds — give customer a clear UI message. Add idempotency + dry-run mode."*

---

## 📚 Reading List
1. Robinhood API docs
2. FINRA / SEC primer
3. r/RobinHood
4. levels.fyi Robinhood