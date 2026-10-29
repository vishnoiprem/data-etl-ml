# Citadel / Citadel Securities — FDE

## Company Snapshot
- **HQ**: Miami, FL / NYC
- **Team Size**: ~50–100
- **Comp**: $200K–$300K; TC $400K–$800K+
- **What they deploy**: Quant + AI deployment teams
- **Travel**: ~0%

## Interview Process
1. Recruiter
2. Coding (medium-hard + probability/stats)
3. ML / market design
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### Quant scenario
**Q:** *"Design a market-making AI deployment."*
**A (winner):** *"C++ price-discovery engine + Python ML model + FIX gateway to exchange. Latency: <1ms order ack. Risk: hard limits in C++, soft in Python. Backtest on 10y of L2 data, walk-forward. PnL attribution by signal. Eval: Sharpe, drawdown, capacity. Deploy with 1% of book for 1 month, scale."*
**Why it worked:** Right quant primitives, risk layered correctly.

---

## ❌ REJECTION STORIES
### Quant scenario
**Q:** *"Strategy blew up."*
**A (loser):** "Tighten the stops."
**What they should have said:** *"Root-cause: post-mortem on signals vs market state. Common: fat-tail event, correlation breakdown, model degeneracy. Add stress tests. Independent risk review."*

---

## 📚 Reading List
1. Citadel engineering blog (limited)
2. *Algorithmic Trading* — Ernest Chan
3. r/quant
4. levels.fyi Citadel