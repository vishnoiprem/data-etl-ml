# Lesson 29: Transformation

> **Week 6 · Day 29 · 90 min**
> **Deliverable:** The 3 phases of a 3-year transformation — foundations, scale, differentiation.

## 🎯 Architect Level
Staff.

## 🧠 Concept

Transformation is the CDO's most-tested skill. The board asks: "can you take us from where we are to where we need to be, in 3 years, without breaking the business?" The answer has 3 phases.

| Phase | Theme | Outcome | Risk |
|---|---|---|---|
| **Y1: Foundations** | Single platform, semantic layer, contracts, governance, 1 AI in production | Reliability + trust | Under-investing in foundations; over-committing on AI |
| **Y2: Scale** | All BUs on the platform, 5-10 AI in production, data products | Adoption + ROI | Over-promising; burning the platform team |
| **Y3: Differentiation** | Externalized data products, agentic AI, board-level reporting | Competitive advantage | Hubris; failing to maintain Y1/Y2 |

The single biggest mistake is to **skip Y1 and jump to Y2/Y3**. "We have AI in production" means nothing if the foundation can't support it. The 18-month "almost AI" failure is the canonical CDO failure.

The second biggest mistake is to **under-invest in change management**. The technology is 30% of the transformation. The change (org, process, incentives, culture) is 70%. The CDO who over-invests in tech under-invests in change.

The third biggest mistake is to **not name the off-ramps**. Each phase has an off-ramp. If Y1 doesn't deliver, kill it and restart. If Y2 doesn't deliver, defer to Y3. The CDO who pretends every phase is on track loses the board.

The change management layers:

1. **Sponsorship** — CEO + board + BU heads visibly behind the change
2. **Incentives** — BU heads measured on data quality, not just data volume
3. **Training** — every BU has a "data champion"; every data person has a "BU partner"
4. **Communication** — monthly all-hands; quarterly board update; weekly exec update
5. **Quick wins** — visible, attributable, celebrated

## 🛠️ Build It

**Spec:** Design the 3-year transformation for the retailer. Name the milestones, the off-ramps, the change management plan.

**Acceptance:**
- 3 phases × milestones
- Off-ramp per phase
- Change management plan (5 layers)
- 3 quick wins
- 1 paragraph on the trade-off (speed vs. adoption)

**Starter:** Use Week 2's 3-year strategy and Week 4's architecture. Add the change management layer.

**Solution (3-year transformation, abridged):**

**Y1: Foundations**
- Milestones: contracts on top 5 sources; semantic layer MVP; 1 AI in production; org restructure
- Off-ramp: if no AI in production by month 12, defer AI portfolio and rebuild
- Quick wins: month-end close 5d → 2h; single source of truth for revenue; data quality scorecard

**Y2: Scale**
- Milestones: all 5 BUs on platform; 5 AI in production; data products to business; CDO in board reporting
- Off-ramp: if BU adoption <50% by month 18, refocus on the bottom 2 BUs before scaling further
- Quick wins: 2nd AI in production; first externalized data product; FinOps dashboard

**Y3: Differentiation**
- Milestones: 10+ AI in production; 1-2 external data products; agentic AI; CDO peer of CFO/CTO
- Off-ramp: if external data product revenue <$XM, kill the externalization
- Quick wins: first $XM in data product revenue; first agentic AI in production

**Change management:**
1. Sponsorship: CEO + board + 5 BU heads signed off; monthly review
2. Incentives: BU heads have data quality + adoption in their scorecard
3. Training: 5 data champions per BU; 5 BU partners per data lead
4. Comms: monthly all-hands; quarterly board update; weekly exec update
5. Quick wins: 3 in Y1, 2 in Y2, 1 in Y3

## 🏛️ Architect Notes

- **Trade-off:** Speed vs. adoption. Default: adoption. A platform the BUs don't use is a platform that doesn't exist.
- **Capacity / cost:** Change management is 30% of the CDO's calendar. Plan for it; protect the time.
- **When NOT to use:** Don't run a transformation during a reorg or a downturn. The org change absorbs all the oxygen. Sequence: org stable → transform.
- **Production checklist:**
  - [ ] 3 phases × milestones
  - [ ] Off-ramp per phase
  - [ ] 5 change management layers
  - [ ] 3 quick wins
  - [ ] Trade-off paragraph

## 🌙 Reflect

- Which phase is the most likely to slip? Why? Pre-write the answer.
- Which BU head would resist the most? What would you do?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 30 — Vendor and financial management.