# 71. Bloomberg

- **Role:** Senior ML Engineer (Financial NLP / market data)
- **Tech stack:** Python, C++, PyTorch, NLP, kdb+, Solr, Bloomberg Terminal stack
- **Comp band:** $200K-$500K base + bonus (no public equity)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, mission fit | 30 min | ~50% |
| 2. Technical phone | Coding + ML + finance basics | 60 min | ~40% |
| 3. Onsite (4 rounds) | Coding, system design, ML, behavioral | 4-5 hrs | ~30% |
| 4. Hiring committee | Cross-team review | 1-2 wks | ~60% |
| 5. Offer | Comp, bonus | 1 wk | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Bloomberg?"
**Answer:** "Bloomberg is the only company that owns the entire financial information stack — news, market data, analytics, terminal. I want to apply ML where the data is real-time, multi-modal, and the bar for accuracy is trader trust, not benchmark accuracy."
**Tip:** Show you've used the Terminal and understand the editorial + data business.

### Q1.2: "What's your favorite Bloomberg AI feature?"
**Answer:** "IB Chat, the in-terminal RAG. It's a 30-year moat — Bloomberg owns the document corpus, the data feed, and the user. That's a closed loop no one else can build."
**Tip:** Reference a specific product. Bloomberg wants people who use the Terminal.

## Stage 2: Technical phone screen

### Q2.1: Merge intervals.
**Answer:**
```python
def merge(ivs):
    ivs.sort()
    out = [ivs[0]]
    for s, e in ivs[1:]:
        if s <= out[-1][1]: out[-1][1] = max(out[-1][1], e)
        else: out.append([s, e])
    return out
```
**Tip:** Standard; they want clean code.

### Q2.2: How would you build a sentiment classifier for financial news?
**Answer:** Fine-tune FinBERT on a labeled corpus, add entity linking to tickers, calibrate for sector-specific language, evaluate against market reactions (next-day returns).
**Tip:** They care about backtested correlation with market moves.

## Stage 3: Onsite

### Round 3.1: Coding
**Q:** Implement an LRU cache + a rate limiter combined.
**Answer:** Two data structures; discuss the trade-off.

### Round 3.2: System design
**Q:** Design a real-time news feed that auto-tags entities and topics.
**Answer:** Kafka → NER service (FinBERT) → topic classifier → entity linker (Wikidata + tickers) → tag store → Terminal UI. Latency target: <500ms p99.

### Round 3.3: ML deep-dive
**Q:** How would you evaluate a financial NER model?
**Answer:** Precision/recall on CoNLL-2003 + custom financial entities, backtest on earnings calls, monitor drift on breaking news.

### Round 3.4: Behavioral
**Q:** Tell me about a project that required cross-team coordination.
**Answer:** STAR with multiple stakeholders.

## Stage 4: Hiring committee
Panel of senior engineers + research lead + product. They look for: (1) financial domain intuition, (2) production ML at scale, (3) editorial respect.

## Stage 5: Offer
No public equity. Base is competitive with FAANG. Annual bonus is significant (15-30% of base). They rarely negotiate above band.

## Tips for the Bloomberg loop
- Read the Bloomberg Terminal if you can.
- Know the difference between "news," "data," and "analytics" products.
- Practice entity linking, NER, and sentiment tasks.
- Show financial domain knowledge (earnings, filings, market microstructure).
- Be ready to defend every "would a trader trust this?" decision.
- They value shipping over research prestige.

## Real candidate report
> "Four rounds: 2 coding, 1 system design, 1 ML. System design was a real-time news feed with entity tagging. They asked finance trivia in behavioral — I prepped with Wall Street Prep. Process took 3 weeks, offer was at the top of band." — Glassdoor, Senior ML Engineer, 2025

## Sources
- [Bloomberg careers](https://www.bloomberg.com/careers)
- [Bloomberg AI research](https://www.bloomberg.com/company/ai)
- [Levels.fyi — Bloomberg](https://www.levels.fyi/companies/bloomberg)
- [Glassdoor — Bloomberg interviews](https://www.glassdoor.com/Interview/Bloomberg-Interview-Questions-E3096.htm)
- [Reddit r/cscareerquestions — Bloomberg](https://reddit.com/r/cscareerquestions)