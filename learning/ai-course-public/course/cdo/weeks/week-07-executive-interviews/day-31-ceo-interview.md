# Lesson 31: CEO interview

> **Week 7 · Day 31 · 90 min**
> **Deliverable:** The 5 most-asked CEO questions, each with a 60-second answer skeleton.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The CEO interview is not a technical interview. It is a leadership, judgment, and strategic-thinking interview. The CEO is asking: "would I want this person in the room when the board challenges the strategy?"

The 5 most-asked CEO questions:

1. **"Tell me about yourself."** (Past → Present → Future, 90 seconds.)
2. **"Why this role? Why this company?"** (Specific motivation, not generic flattery.)
3. **"What's your 3-year plan for data and AI here?"** (Year-by-year; foundations, scale, differentiation.)
4. **"What's the biggest risk you see in our data and AI strategy?"** (Honest, specific, with mitigation.)
5. **"If I gave you $5M, how would you spend it?"** (The portfolio; the ROI; the cuts.)

The single biggest mistake is to **lead with technical depth**. The CEO doesn't care about lakehouse vs. warehouse. The CEO cares about margin, growth, and risk. The CDO who leads with tech loses the room.

The second biggest mistake is to **use jargon**. "We'll deploy a feature store with online and offline serving, integrated with the lakehouse via Iceberg." The CEO stops listening at "feature store." Translate: "we'll make sure the AI has the data it needs in real time."

The third biggest mistake is to **not name the cuts**. The CEO is allergic to wish lists. A plan without cuts is a plan that will never deliver.

## 🛠️ Build It

**Spec:** Build the 5 CEO answers, each in 60 seconds, each with a STAR frame and a follow-up defense.

**Acceptance:**
- 5 questions, 5 answers
- Each answer: 60 seconds, 0 jargon, named cut, named metric
- Each answer: 1 follow-up defense (60 seconds)
- 1 paragraph on the trade-off (depth vs. brevity)

**Starter:** Use your Day 01 introduction, Day 06 strategy, Day 15 prioritization. Synthesize.

**Solution (5 CEO answers, abridged):**

**Q1: Tell me about yourself.**
> "I spent the last 12 years building data platforms and leading data teams — 8 years at Makro leading the data platform transformation, 3 years at Lazada running the real-time customer data platform, and most recently at Xendit scaling the data team from 8 to 30. The through-line is taking fragmented data estates and turning them into platforms the business can build on. I'm here because [specific reason — e.g., this is the next scale of the same problem]."

**Q2: Why this role? Why this company?**
> "Three reasons. One, [specific business challenge — e.g., the AI mandate is real but the foundations aren't there]. Two, [specific company strength — e.g., you have the data volume and the business commitment]. Three, [specific personal motivation — e.g., this is the scale I've been building toward]."

**Q3: What's your 3-year plan?**
> "Year 1 is foundations: single platform, semantic layer, 1 AI in production. Year 2 is scale: all BUs on platform, 5 AI in production, data products to business. Year 3 is differentiation: 10+ AI in production, externalized data products, agentic AI. The hard part is Y1 — if I don't get the foundations right, Y2 and Y3 collapse."

**Q4: What's the biggest risk?**
> "The biggest risk is doing AI before the foundation. The 18-month 'almost AI' failure is the most common pattern. The mitigation: 1 AI in production by month 12, with the foundations in place to scale it. If foundations aren't ready, we defer AI."

**Q5: If I gave you $5M, how would you spend it?**
> "$700K on foundations (contracts, semantic layer, FinOps). $4.3M on the 7-bet portfolio — 2 quick wins, 4 strategic bets, 1 deferred. Total run-rate ROI: $6.5-16M, payback 9-15 months. The cuts: AI customer support, autonomous store replenishment, 8 others — each with a reason."

**Trade-off (depth vs. brevity):** The CEO interview is 60 seconds per answer, 5 answers = 5 minutes. The depth comes in the follow-up. Lead with the headline; defend in the follow-up.

## 🏛️ Architect Notes

- **Trade-off:** Strategic vs. tactical. The CEO wants strategy with enough tactical color to believe you can execute. Default: 80% strategy, 20% tactic.
- **Capacity / cost:** 5 answers × 60 seconds = 5 minutes. The 5 minutes is what gets you the offer.
- **When NOT to use:** Don't answer a CEO question with a slide. The CEO is reading your face, not your deck.
- **Production checklist:**
  - [ ] 5 questions, 5 answers
  - [ ] 60 seconds per answer
  - [ ] 0 jargon
  - [ ] 1 cut named
  - [ ] 1 metric named
  - [ ] 1 follow-up defense per answer

## 🌙 Reflect

- Which answer is your weakest? Re-record.
- Which question would the CEO in your actual interview ask first? Pre-write.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 32 — CTO Interview.