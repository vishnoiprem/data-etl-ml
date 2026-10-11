# 29. SAP (Joule / Business Technology Platform)

- **Role:** ML Engineer / Applied Scientist (Joule, BTP AI, S/4HANA ML)
- **Tech stack:** Python, PyTorch, TensorFlow, Java, ABAP (sometimes), HANA, SAP BTP, Kubernetes
- **Comp band:** $180K-$500K (IC3-IC5); senior crosses $650K+; RSUs + bonus, EUR-equivalent
- **Cumulative pass rate:** ~3-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Org match (Joule/BTP/S4), comp, location | 1 week | ~55% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML | 1-2 weeks | ~45% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML, behavior | 1-2 days | ~35% advance |
| 4. **Hiring committee (Tech Panel)** | Cross-org panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why SAP for AI?"
**Answer:** "Joule is the AI copilot for the world's business data. SAP has 400K+ customers running their ERP, finance, and supply chain on our systems. Building agents that reason over that data — invoices, purchase orders, HR records — is the most strategic AI deployment in enterprise."
**Tip:** Reference *Joule*, *BTP*, *S/4HANA* — not generic AI. SAP has the deepest enterprise data moat.

### Q1.2: "Tell me about a time you built a model for a global enterprise"
**Answer:** STAR with focus on *data variety, language localization, and integration with legacy systems*. SAP customers run heterogeneous stacks.
**Tip:** Show enterprise empathy. SAP sells to global Fortune 500s with complex integrations.

## Stage 2: Technical phone screens (90 min)

### Q2.1: Coding: "Longest substring without repeating characters"
**Answer:** Sliding window with a set, O(N).
```python
def lengthOfLongestSubstring(s):
    seen, l, best = set(), 0, 0
    for r, c in enumerate(s):
        while c in seen:
            seen.remove(s[l]); l += 1
        seen.add(c)
        best = max(best, r - l + 1)
    return best
```
**Tip:** LeetCode mediums. Some roles use Java.

### Q2.2: ML: "Design a cash-flow forecasting model for an ERP system"
**Answer:** (1) Features — historical cash flow, AR/AP aging, seasonality, customer payment history, supplier terms, FX rates; (2) Multi-horizon forecast (7/30/90 days); (3) Model — Temporal Fusion Transformer or DeepAR for multivariate time series; (4) Confidence intervals via quantile regression; (5) Integration with S/4HANA tables; (6) Drift monitoring; (7) Explainability for finance teams.
**Tip:** SAP has a "Business AI" focus — show *business* value, not just model accuracy.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min, 2 questions)
- Q: Product of array except self. O(N) with prefix/suffix.
- Q: Validate BST. In-order traversal, O(N).
- Optional 3rd: SQL on joins, window functions, and complex aggregations.

### Round 3.2: System design (60 min)
- Q: Design Joule, an AI copilot for SAP BTP. Multi-tenant LLM serving, RAG over customer ERP data, action tool registry (Create PO, Approve Invoice), guardrails, multi-language (40+ languages), and audit.
- Q: Design a feature store on SAP HANA. Native HANA feature engineering, point-in-time joins, batch + streaming, and integration with S/4HANA.

### Round 3.3: ML deep-dive (60 min)
- Q: How would you build a RAG system that respects ERP authorization? Per-user ACL filter at retrieval, customer-specific data isolation, and citation with row-level provenance.
- Q: How would you fine-tune a model for SAP's procurement use case? SFT on historical PO data, RLHF with finance expert rewards, multi-language (German, Japanese, English), bias check, and audit.

### Round 3.4: Behavioral (60 min)
- Q: Tell me about a time you worked across cultures. SAP is global. Germany, India, and US teams are common.
- Q: A time you had to ship within SAP's release cycle (quarterly releases).
- Q: Disagreement with a stakeholder on a model design.

## Stage 4: Hiring committee
A panel of senior engineers + product reviews. They look for: (1) ML bar for the level, (2) enterprise + business-process depth, (3) SAP values (Help, Build, Believe), (4) cross-cultural collaboration. Vote is "Strong Hire / Hire / No Hire / Strong No Hire." Hiring manager has tie-breaker.

## Stage 5: Offer
Cash + RSUs + bonus. SAP is competitive in Europe (Walldorf, Munich) but lower for US-based hires. Negotiation is moderate. Team match after loop. Some roles are remote-EU-only.

## Tips for the SAP loop
- Reference *Joule*, *BTP*, *S/4HANA*, *HANA Cloud* by name.
- For ML rounds, emphasize *business process knowledge* — SAP is workflow + data.
- For system design, multi-language + multi-region is a real constraint.
- For behavioral, SAP values "Build" — show you ship iteratively, not in big-bang.
- Java + SQL are heavily used. Some roles want ABAP knowledge.
- Be ready to discuss ERP concepts — GL, AP, AR, MM, SD.
- Localization is a real concern — show you've thought about non-English markets.

## Real candidate report
> "Loop for Joule (BTP AI). 4 rounds in 1 day, virtual. Coding was 2 mediums. System design was a multi-tenant LLM agent for SAP with RAG over ERP tables and they wanted ACL filtering at the SQL level. ML deep-dive was on fine-tuning for German-language procurement. Behavioral was 'Build' flavored. Offer at IC4, ~$340K total, 6 weeks." — r/sap, 2025-08

## Sources
- [SAP Careers](https://jobs.sap.com/)
- [Levels.fyi SAP salaries](https://www.levels.fyi/companies/sap/salaries)
- [SAP AI Blog](https://blogs.sap.com/tag/artificial-intelligence/)
- [Joule docs](https://www.sap.com/products/artificial-intelligence/joule.html)
- [Glassdoor SAP interviews](https://www.glassdoor.com/Interview/SAP-Interview-Questions-E10471.htm)
