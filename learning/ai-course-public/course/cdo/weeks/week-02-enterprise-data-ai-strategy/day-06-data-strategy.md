# Lesson 6: What is a data strategy?

> **Week 2 · Day 6 · 90 min**
> **Deliverable:** A 1-page data strategy.

## 🎯 Architect Level
Staff.

## 🧠 Concept

A data strategy is **not** a technology plan. A technology plan describes what you'll build. A data strategy describes what business decisions will improve, what capabilities are required to improve them, who owns each capability, and what ROI the business should expect.

The four components, in order:

1. **Business decisions to improve** — name 5-10 decisions the business makes (or should make) where better data would change the outcome. These are the *demand* for data.
2. **Required capabilities** — for each decision, what data, what models, what integrations, what governance are required. These are the *supply*.
3. **Accountable owners** — for each capability, a single person who is accountable. The data team is rarely the owner; the business is. The data team is the *enabler*.
4. **Measurable ROI** — for each decision, what the expected business outcome is, with a number, a baseline, and a time horizon.

The single biggest failure mode is to **start with capabilities** ("we need a lakehouse, we need ML, we need a data mesh"). Capabilities without decisions are solutions looking for problems. CEOs will not fund them.

The second biggest failure is to **skip the owners**. If the data team owns the outcome, the business will not engage. The data team enables; the business owns.

## 🛠️ Build It

**Spec:** Produce a 1-page data strategy for a hypothetical Series-D retailer with $2B revenue.

**Acceptance:**
- 1 page (300-500 words)
- 5-10 named business decisions
- For each decision: capability, owner, ROI
- The 1-page is the only artifact; the 50-page appendix is the implementation plan

**Starter:** Use your work at Makro as the reference shape. The "fragmented data across 5 BUs" is the canonical Series-D retailer problem.

**Solution (1-page, abridged):**

> **Decisions to improve**
> 1. Pricing — what to charge per SKU per region per hour
> 2. Inventory — what to stock per store per week
> 3. Promotion — what to discount and when
> 4. Assortment — what to carry per store
> 5. Last-mile fulfillment — how to route
> 6. Customer retention — who to target with what offer
> 7. Vendor negotiation — what's the leverage
> 8. Capex allocation — where to open, where to close
> 9. Risk — which credits, which exposures
> 10. CEO reporting — what the board sees on day 5
>
> **Capabilities, owners, ROI** (selected)
> | Decision | Capability | Owner | ROI |
> |---|---|---|---|
> | Pricing | Real-time feature store, ML serving | VP Pricing | +1-3% margin, $20-60M/yr |
> | Inventory | Demand forecasting, scenario modeling | VP Supply Chain | −10-20% stockouts, $X/yr |
> | Promotion | Uplift modeling, A/B framework | VP Marketing | +5% promo ROI |
> | Last-mile | Routing optimization, real-time traffic | VP Logistics | −10% delivery cost |
> | Retention | Customer 360, propensity, next-best-offer | VP CRM | +2-5% retention |
> | CEO reporting | Single semantic layer, KPI catalog | CFO | Day 5 → Day 2 close |
>
> **Foundation capabilities (owned by CDO)**: data contracts, data quality SLAs, governance, security, FinOps. These are not "deliverables" — they are the conditions for the above to work.

## 🏛️ Architect Notes

- **Trade-off:** Long strategy doc (50 pages) vs. 1-page strategy + 50-page appendix. 1-page. The 1-page is what the CEO signs.
- **Capacity / cost:** A 1-page strategy is 300-500 words. The appendix is the implementation plan; the 1-page is the contract.
- **When NOT to use:** Don't write a 1-page strategy for a business unit that doesn't have a CEO. Use the longer form for a department.
- **Production checklist:**
  - [ ] 5-10 named business decisions
  - [ ] Owner is a business role, not a data role
  - [ ] ROI has a number, a baseline, and a time horizon
  - [ ] Foundation capabilities named separately
  - [ ] 1 page, 0 tech jargon in the decision rows

## 🌙 Reflect

- Which of your 5-10 decisions would the CEO push back on hardest? Pre-write the answer.
- Which owner would push back on being named? Pre-write the conversation.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 7 — Enterprise Data Operating Model.
