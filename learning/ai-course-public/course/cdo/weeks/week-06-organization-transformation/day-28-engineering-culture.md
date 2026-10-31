# Lesson 28: Engineering culture

> **Week 6 · Day 28 · 90 min**
> **Deliverable:** The 8 traits of a high-performing data org, each with a measurable behavior.

## 🎯 Architect Level
Staff.

## 🧠 Concept

Culture is the hardest thing to copy and the hardest thing to build. It is also the single biggest predictor of whether the team ships. The CDO who builds culture builds a team that compounds; the CDO who doesn't builds a team that churns.

The 8 traits of a high-performing data org:

| # | Trait | What it looks like | Measurable behavior |
|---|---|---|---|
| 1 | **Ownership** | "I own the outcome, not the deliverable." | % of incidents owned end-to-end by the team |
| 2 | **Data quality** | "We don't ship data we don't trust." | DQ scorecard trend; % of incidents from bad data |
| 3 | **Reliability** | "We meet our SLOs, and we tell you when we don't." | SLO achievement; error budget burn rate |
| 4 | **Velocity** | "We ship continuously, in small increments." | Deploy frequency; lead time for changes |
| 5 | **Documentation** | "If it isn't documented, it doesn't exist." | % of services with README; % of dashboards with owner |
| 6 | **Collaboration** | "We work with the business, not at them." | NPS from BU; % of projects with BU co-owner |
| 7 | **Learning** | "We blameless-postmortem and we share what we learn." | Postmortems per quarter; % with action items completed |
| 8 | **Craft** | "We sweat the details; we take pride in the work." | Code review depth; design review attendance |

The single biggest mistake is to **list the traits but not measure them**. "We value ownership" is a poster; "ownership is measured by X" is culture. The CDO who measures the traits is the CDO who shapes them.

The second biggest mistake is to **set the bar at "shipping fast."** Speed without reliability is a liability. The right pair is "shipping fast AND reliably." Both matter.

The third biggest mistake is to **not model the behavior yourself**. Culture is top-down. The CDO who is on-call, who runs the postmortem, who writes the doc, who sits in the design review — that CDO builds culture. The CDO who delegates all of it does not.

## 🛠️ Build It

**Spec:** Pick 3 of the 8 traits. For each, design the measurable behavior and the cadence.

**Acceptance:**
- 3 traits chosen (with reason)
- Measurable behavior per trait
- Cadence (weekly / monthly / quarterly)
- Owner per trait
- 1 paragraph on the trade-off (rigor vs. speed)

**Starter:** Pick the 3 that the role most needs. For a CDO interview, that's usually ownership, data quality, and collaboration.

**Solution (3 traits, abridged):**

**Trait 1: Ownership**
- Behavior: every incident has a named owner who drives the resolution and writes the postmortem
- Metric: % of incidents with a named owner at +15 min; % of postmortems with action items completed in 30 days
- Cadence: weekly incident review; quarterly ownership survey
- Owner: incident commanders (rotating) + CDO (escalation)

**Trait 2: Data quality**
- Behavior: every shipped dataset has a DQ scorecard with an SLO
- Metric: % of production datasets with a scorecard; DQ SLO achievement
- Cadence: daily automated checks; monthly DQ review; quarterly data council
- Owner: data engineering leads; CDO escalates

**Trait 3: Collaboration**
- Behavior: every project has a named BU co-owner
- Metric: % of projects with BU co-owner; BU NPS (quarterly survey)
- Cadence: monthly BU review; quarterly NPS survey; annual planning with BUs
- Owner: PMO + chief of staff

**Trade-off (rigor vs. speed):** The traits pair up. Reliability + velocity. Documentation + collaboration. The CDO holds both, communicates both, and never pits one against the other.

## 🏛️ Architect Notes

- **Trade-off:** Measure vs. feel. Measure 3 things deeply; feel the rest. Over-measuring is bureaucracy.
- **Capacity / cost:** A culture program is mostly CDO time, not budget. The investment is in the rituals (postmortems, design reviews, 1:1s, all-hands).
- **When NOT to use:** Don't survey the team on culture. The survey tells you what they think you want to hear. Measure the behaviors.
- **Production checklist:**
  - [ ] 3 traits chosen
  - [ ] Measurable behavior per trait
  - [ ] Cadence
  - [ ] Owner
  - [ ] Trade-off paragraph

## 🌙 Reflect

- Which trait is your weakest? What would you do about it?
- Which trait is your strongest? Why?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 29 — Transformation.