# Lesson 14: Commercial AI use cases

> **Week 3 · Day 14 · 90 min**
> **Deliverable:** 8 commercial AI patterns with $ ranges and decision rights.

## 🎯 Architect Level
Senior.

## 🧠 Concept

There are 8 commercial AI patterns that recur across industries. The CDO who knows them can pattern-match the playbook when the interviewer asks "what would you do here?"

1. **Demand forecasting** — predict future demand at SKU/store/region level. Cost-out: inventory + markdowns. Revenue-up: availability.
2. **Customer 360 / personalization** — single view of customer; next-best-offer; recommendation. Revenue-up: conversion, AOV, retention.
3. **Dynamic pricing** — price elasticity, competitive pricing, markdown optimization. Revenue-up: margin.
4. **Credit / risk decisioning** — underwriting, collections, fraud, AML. Cost-out: losses, ops.
5. **Churn / retention** — predict churn propensity, intervene. Revenue-up: NRR, retention.
6. **Document intelligence (RAG)** — extract, summarize, classify unstructured content. Cost-out: ops, cycle time.
7. **AI customer support** — deflect tickets, assist agents. Cost-out: support cost, handle time.
8. **Forecasting for ops** — workforce, supply chain, capacity. Cost-out: opex, SLA.

Each pattern has:
- A typical $ range (low / mid / high)
- A typical readiness profile
- A typical risk profile
- A typical owner

The patterns are the menu. The portfolio is what you pick from the menu given the company's data, maturity, and risk tolerance.

## 🛠️ Build It

**Spec:** Build the 8-pattern menu with $ ranges, readiness, risk, and owner.

**Acceptance:**
- 8 patterns named
- $ range (low/mid/high) per pattern with [CONFIRM] where needed
- Readiness profile (ready/partial/not)
- Risk profile (low/medium/high)
- Owner (data team vs. business)

**Starter:** Use the 8 patterns above. Calibrate against your resume evidence.

**Solution (8 patterns):**

| Pattern | $ range | Readiness | Risk | Owner |
|---|---|---|---|---|
| Demand forecasting | $0.5-5M margin | Ready | Wait | Yes | Low | Data + merch |
| Customer 360 / NBO | $1-10M revenue | Partial | Months | Medium | Data + marketing |
| Dynamic pricing | $0.5-3M margin | Partial | Months | Medium | Data + merch |
| Credit / risk decisioning | $1-20M losses | Ready | Months | Medium | Data + risk |
| Churn / retention | $0.5-5M revenue | Partial | Months | Medium | Data + CS |
| Document intelligence (RAG) | $0.5-5M ops | Ready | Months | Medium | Data + ops |
| AI customer support | $0.5-3M support | Partial | Quarters | High | Data + support |
| Ops forecasting | $0.2-2M opex | Ready | Weeks | Low | Data + ops |

The point is the shape. Each row has $ range, readiness, complexity, risk, and owner. When the interviewer asks "what's the highest-ROI AI use case in this business?", you pull from this menu and pattern-match.

## 🏛️ Architect Notes

- **Trade-off:** Build vs. buy. The 8 patterns above can all be built in-house, but several (RAG, support) often start with vendor (OpenAI, Anthropic, Cohere, vendor RAG platforms). Default: build the data + feature layer; rent the model + UI.
- **Capacity / cost:** Each pattern costs 4-8 FTE-quarters to build. A 5-pattern portfolio is 20-40 FTE-quarters — i.e., a 10-15 person team for 1-2 years.
- **When NOT to use:** Don't pick patterns off the menu without knowing the company's data maturity. A churn model on bad data is worse than no churn model.
- **Production checklist:**
  - [ ] 8 patterns named
  - [ ] $ range per pattern
  - [ ] Readiness profile
  - [ ] Risk profile
  - [ ] Owner
  - [ ] Build vs. buy noted

## 🌙 Reflect

- Which pattern is your strongest (you've shipped it)? Which is your weakest?
- Which pattern would the CEO push first? Pre-write the answer.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 15 — Investment prioritization.