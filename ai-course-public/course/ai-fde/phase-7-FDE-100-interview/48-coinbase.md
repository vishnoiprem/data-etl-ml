# Coinbase — Crypto / Base Agent FDE

## Company Snapshot
- **HQ**: Remote / NYC
- **Team Size**: ~30–60
- **Comp**: $180K–$240K; TC $300K–$500K
- **What they deploy**: Crypto / Base agent deployments
- **Travel**: 10–25%

## Interview Process
1. Recruiter
2. Coding (medium)
3. Crypto / agent system design
4. Loop — coding, customer scenario

---

## ✅ SUCCESS STORIES

### Crypto scenario
**Q:** *"Customer wants Coinbase Prime integration with their trading system."*
**A (winner):** *"Coinbase Prime API: portfolio read, orders, balances, custody. JWT-signed requests, nonce management. WebSocket for market data + fills. Testnet first. Reconciliation pipeline with daily snapshots. SLA: 99.95% uptime. Compliance: SOC2 + NYDFS."*
**Why it worked:** Coinbase-native (Prime API, JWT, WS), compliance-aware.

---

## ❌ REJECTION STORIES
### Crypto scenario
**Q:** *"Order mismatches."*
**A (loser):** "Add retries."
**What they should have said:** *"Idempotency keys, order state machine (pending → filled / canceled / rejected), persistent store of all orders, daily reconciliation report. Slack alert on drift."*

---

## 📚 Reading List
1. Coinbase docs (Advanced Trade API, Prime)
2. WebSocket reconciliation patterns
3. r/CoinBase
4. levels.fyi Coinbase