# Sonar — Engineering Director (Singapore) — Technical Round Prep

> No resume was provided, so example answers use **placeholders** — swap in your real systems, scale numbers, and tech stack before the interview. For a Director-level technical round, expect breadth + judgment over deep coding — they're testing architecture thinking, technical leadership, and how you make engineering tradeoffs, not LeetCode.

---

## 1. What This Round Likely Tests
Based on the JD, the technical bar for this role centers on:
- **Architecture & technical direction** for a multi-team product
- **Java / JavaScript** (or equivalent) depth — enough to be credible with senior engineers, not necessarily hands-on daily
- **Agile, CI/CD, automated testing** practices at org scale
- **Engineering quality standards** (fitting, given Sonar's own product is code quality/verification)
- **Scaling teams and systems together** — architecture decisions that survive org growth

---

## 2. Likely Questions & How to Answer

### Q1: "Walk me through a system or architecture you designed or owned end-to-end."
**Approach:** Pick your most senior architecture decision. Structure as Context → Constraints → Options considered → Decision → Outcome/lessons.
> Example skeleton: "We had [system] hitting [bottleneck — scale/latency/cost] at [N requests/day]. I evaluated [option A vs B vs C], chose [X] because [tradeoff reasoning], and it resulted in [measurable outcome]. In hindsight, I'd [one honest lesson learned]."
**Why it matters here:** Sonar cares about *explainable, defensible* decisions — mirror that in how you reason out loud.

### Q2: "How do you ensure code quality and maintainability across multiple squads, especially with AI-assisted development on the rise?"
**Approach:** This is almost certainly asked given Sonar's product is literally AI code verification — show you've thought about it, even informally.
> "I enforce quality gates in CI (static analysis, test coverage thresholds, mandatory review), and increasingly I think about how AI-generated code changes the risk profile — it can look syntactically fine but introduce subtle logic, security, or maintainability issues at a much higher volume than humans alone. I'd want tooling like Sonar's own product in the pipeline, not just relying on review."

### Q3: "Tell me about your experience with Java / JavaScript (or your core stack)."
**Approach:** Be honest about current hands-on depth vs. leadership-level fluency. Directors aren't expected to be writing daily code, but should be able to read a PR/design doc and ask sharp questions.
> "I'm hands-on less often day-to-day now, but I still review architecture docs and critical PRs, and I'm fluent enough in [language] to pair with engineers when debugging cross-team issues or evaluating a tricky design tradeoff."

### Q4: "How do you structure CI/CD and automated testing across teams you lead?"
**Approach:** Cover pipeline stages (lint → unit → integration → security/static analysis → deploy gates), ownership model (platform team vs. each squad owns their pipeline), and how you measure health (deploy frequency, change failure rate, lead time — DORA metrics).

### Q5: "Describe a time you had to make a build-vs-buy or technology choice that your teams disagreed with."
**Approach:** STAR, emphasizing how you gathered input, made the call, and communicated it (Sonar's culture value "Deliberate in our decisions" — show rigor, not just authority).

### Q6: "How do you handle technical debt vs. feature delivery pressure across multiple squads?"
**Approach:** Show a system, not just an opinion — e.g., fixed % of sprint capacity for debt, debt visible on the roadmap, escalation path when debt risks an outage.

### Q7: "How would you approach onboarding into Sonar's product/tech stack, given you'd be leading teams building an AI code-verification platform?"
**Approach:** Show humility + a plan — first 30/60/90 days: deep dive into SonarQube architecture, shadow on-call, meet each EM and squad, audit current quality/CI metrics before changing anything.

### Q8: "How do you evaluate engineering productivity/output across a team you lead, especially with AI coding tools now in the mix?"
**Approach:** Avoid naive metrics (lines of code, PR count). Talk DORA metrics, outcome-based goals, and qualitative signals (code review quality, incident rates) — and that AI-generated code volume makes *verification* metrics (e.g., defect/regression rate) more important than raw throughput.

### Q9 (Possible system design prompt): "How would you design a scalable static-analysis pipeline that processes code from thousands of repos with low latency?"
**Approach for system design under time pressure:**
1. Clarify scale (repos, commit frequency, languages supported)
2. Ingestion (webhook/event-driven on commit/PR)
3. Analysis workers (queue-based, horizontally scalable, language-specific analyzers)
4. Caching/incremental analysis (only re-analyze changed files/modules)
5. Results storage + dashboard/API
6. Discuss tradeoffs: latency vs. cost, false positive tuning, multi-tenancy isolation

---

## 3. Questions You Could Ask Them (technical-flavored)
1. "What does the current architecture for the Foundation Agent or SonarSweep look like at a high level — is it more rules/static-analysis based or model-driven?"
2. "What's the biggest technical challenge the Singapore team is currently facing — scale, latency, or something else?"
3. "How do engineering teams here use AI coding agents internally, and how do you verify that code yourselves?"

---

## 4. Prep Checklist
- [ ] Pick your strongest architecture story and rehearse it in under 3 minutes
- [ ] Pick one tech-debt-vs-delivery story
- [ ] Refresh on DORA metrics (deploy frequency, lead time, change failure rate, MTTR)
- [ ] Be ready to sketch a simple system design on a whiteboard/screen-share
- [ ] Have an honest, confident answer for "how hands-on are you still, technically?"
