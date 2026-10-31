# Lesson 38: Technical leadership simulation

> **Week 8 · Day 38 · 90 min**
> **Deliverable:** The architecture defense, rehearsed end-to-end in 30 minutes.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The technical leadership simulation is the CTO / architect round. The interviewer is testing: "can this person make technology decisions I can defend?" The bar is not "can this person write code." The bar is "can this person own the architecture, the build-vs-buy, the trade-offs, and the consequence."

The 5 sections of the 30-minute defense (per Week 4's case study):

1. **Diagnosis** (3 min) — the state of the platform today
2. **Target architecture** (10 min) — 5 layers + cross-cutting + AI
3. **Build-vs-buy** (5 min) — 12 choices justified
4. **Security posture** (5 min) — 5 controls + AI Act
5. **Cost trajectory** (5 min) — $XM today, $YM Y1, $ZM Y3
6. **Q&A** (2 min) — defend the rejected alternatives

The single biggest mistake is to **draw the architecture on the fly**. The CDO who fumbles the diagram loses the room. Practice the diagram until it's muscle memory.

The second biggest mistake is to **not name the rejected alternatives**. The CTO will ask "why not Snowflake?" If you don't have an answer, you've lost.

The third biggest mistake is to **not show the cost trajectory**. The CTO and the CFO both want to know the bill. The CDO who doesn't have the trajectory loses the budget conversation.

## 🛠️ Build It

**Spec:** Rehearse the architecture defense end-to-end. Time yourself. Find the weak sections.

**Acceptance:**
- 30 minutes, no overrun
- 5 layers drawn and named
- 12 build-vs-buy choices justified
- 5 security controls named
- Cost trajectory named with $X, $Y, $Z
- "Why not [alternative]?" answered
- 1 paragraph on the trade-off (depth vs. brevity)

**Starter:** Use Case Study 4 from Week 4. Time yourself.

**Solution (rehearsal plan, abridged):**

| Section | Target | Actual | Gap |
|---|---|---|---|
| Diagnosis | 3 min | 3.5 min | Trim 30 sec |
| Architecture | 10 min | 12 min | Cut 1 layer of detail |
| Build-vs-buy | 5 min | 4 min | Add 1 rejected alternative |
| Security | 5 min | 5 min | OK |
| Cost | 5 min | 6 min | Trim 1 min |
| Q&A | 2 min | (skip) | Practice at least 3 follow-ups |

Re-record. Find the 2 weakest sections. Rewrite. Re-rehearse.

**Trade-off (depth vs. brevity):** The CTO interview rewards depth. Default: 30% headline, 60% depth, 10% alternatives. The 30-minute defense is your moment to show the depth you can't show in the CEO room.

## 🏛️ Architect Notes

- **Trade-off:** Architecture detail vs. business context. The CTO wants the detail; the room has limited time. Lead with the headline, defend in the follow-up.
- **Capacity / cost:** A 30-minute architecture defense takes 6-8 hours to build + rehearse. Spread over 2-3 sessions.
- **When NOT to use:** Don't read the architecture. The CTO can read. The CTO is reading your face.
- **Production checklist:**
  - [ ] 30 minutes, no overrun
  - [ ] 5 layers drawn
  - [ ] 12 build-vs-buy justified
  - [ ] 5 security controls
  - [ ] Cost trajectory
  - [ ] 3 follow-ups rehearsed
  - [ ] Trade-off paragraph

## 🌙 Reflect

- Which section is your weakest? Re-record.
- Which alternative would the CTO challenge first? Pre-write.
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 39 — Executive case.