# Engineering Manager (EM) Interview — Canonical Questions

> 245 community-reported EM interview questions, 2026 vintage. Use these
> as the spine of the EM tracks (`em_introduction/`, `people_management/`,
> `project_retrospective/`) — don't fabricate questions; use this list.

---

## System Design (74 questions)

These are full system design rounds. They overlap heavily with the
existing `system_design/` track — point EM-track students to that
service for the working services, and use the lessons here to add
**EM-specific framing** (tradeoffs about team size, on-call, sprint
planning, stakeholder management baked into the design).

Sample questions:

- Design a trend aggregator
- Design an inference batching system for a single GPU (up to 100
  inputs/batch, sync wait, max utilization)
- Design Instagram
- Design a system to deny services to requests from banned IPs (gov.x)
- Design a system to show top 10 most frequently listened songs in the
  last 7 days
- Design a metrics and logging service
- Design a system architecture for WhatsApp
- Design a ranked cache system
- Design a banking system (account creation, deposits, transfers, top
  active accounts)
- Design Dropbox / S3 / etc.

## People Management (22 questions)

Sample questions:

- Tell me about a time you had a conflict with someone. How did you
  resolve it and what did you learn? (39 community answers)
- How would you handle an engineer who creates conflict with team
  members but is still performing well?
- Why did you choose Engineering Manager as a career path?
- Tell me about a time when you dealt with a conflict with engineers.
- Tell me about a time when you had a disagreement with your manager.

Patterns to cover in `people_management/04_performance_management/`:
- High-performer-with-friction cases
- Conflict mediation
- Career path conversation (IC vs Manager)

## Technical (23 questions)

Sample questions:

- How would you build TinyURL?
- Design a metrics and logging service.
- How would you store a list of numbers as a single number? (5y ago,
  but a classic)
- Design the system architecture for WhatsApp.
- Tell me about a technical challenge that you have overcome.

Pattern: EMs aren't expected to code in detail, but they ARE expected
to reason about architecture at a high level. These are
**architecture-judgment** questions, not "implement a sorted list".

## Coding (14 questions)

Sample questions:

- Design and implement a ranked cache system
- Design a banking system to facilitate account creation, deposits,
  transfers, top active accounts (CSV/JSON command parser)
- Maximum Number of Visible Points
- How would you store a list of numbers as a single number?
- How would you sort a bitonic array efficiently?

Pattern: simple systems (TinyURL, LRU, Bitonic sort) coded in 30-45
min. Add light code samples in lessons; full solutions live in
`coding_interviews/`.

## Behavioral (131 questions — the bulk)

Sample questions:

- Tell me about a time when you handled a difficult stakeholder
  (104 community answers)
- Tell me about a time you made a mistake (117 community answers)
- How would you respond if your team disagreed with your ideas?
- Tell me about a time you had a conflict with someone. How did you
  resolve it and what did you learn?
- Tell me about a time when you worked on a project with a tight
  deadline.

EM behavioral themes:
- **Stakeholder management** (cross-functional, up, down, sideways)
- **Difficult people** (high-performer conflict, low-performer
  management)
- **Mistakes & learning** (yours AND your team's)
- **Disagreement** (with your manager, your team, your peer managers)
- **Deadline pressure** (shipping on time, scope cuts, pushback)
- **Career** (why EM, IC→manager transition, mentoring)

---

## Use this in the EM tracks

When building `em_introduction/`, `people_management/`, and
`project_retrospective/`, mine this list for canonical prompts.
Don't invent brand-new questions. The community has already validated
these as real.

The `project_retrospective/` module should specifically feature 3-5
fully-written example PRs from the behavioral bucket above, walked
through with STAR + an EM-specific lens (what you learned as a
manager, not just as an IC).
