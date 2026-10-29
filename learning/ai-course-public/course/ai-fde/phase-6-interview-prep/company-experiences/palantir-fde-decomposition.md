# Palantir FDE — Decomposition + Learning (the canonical FDSE loop)

> **Source:** Palantir FDE/FDSE interview guide, posted on an interview-prep platform, updated 8 days before this writeup. Synthesized from **3 interview experiences and 23 questions** by a Senior Technical Contributor with direct input from Palantir candidates. **Palantir is the company that invented the decomposition round; this is the loop to prep for if you want to do FDE work at any company with a Palantir lineage (Anthropic, OpenAI, AWS FDE, Rippling, Kepler, Contour).**

---

## 1. What was the loop?

The Palantir FDE loop is **4 stages over 3-4 weeks**. The candidate applies to a broad engineering track; team matching happens AFTER the onsite.

| Stage | Length | What they tested | What they wanted |
|---|---|---|---|
| 1. Recruiter call | 30 min | Background, motivation, project self-awareness, culture fit | "Genuine motivation + mission alignment + long-term fit" — NOT generic enthusiasm |
| 2. Technical screen | 60 min | Live coding in CodePair/Karat OR HackerRank (coding + SQL + API task) | "Clarifying instincts + end-user framing + trade-off reasoning + clean communication" |
| 3. Onsite | 3 × 60 min | 3 rounds drawn from a POOL: decomposition, learning, coding, re-engineering, system design | Decomposition is nearly universal; learning is often paired with it; behavioral is EMBEDDED in every round (15-20 min) |
| 4. Hiring manager | 60 min | Revisits a weaker area from the onsite; team matching happens here | "Resolved doubts + depth of ownership + self-reflection + mission conviction" |

**The 3-round pool is the most distinctive part.** No two candidates see the same combination. You need to prep all 5 formats without knowing which 3 you'll get.

**The candidate's framing (per the guide):** "Palantir builds its forward deployed engineer interview around a skill most big-tech loops barely test: breaking a vague, real-world challenge into parts you can actually build. Two of its rounds, decomposition and learning, have no direct equivalent at most FAANG+ companies."

**The Palantir-specific signal:** AI is **prohibited** throughout the entire loop. Plan to solve every coding, decomposition, and learning challenge without AI assistance. (This is the opposite of the OpenAI FDE loop, which has the AI-enabled coding screen.) Behavioral questions are EMBEDDED in nearly every round rather than in a separate interview.

---

## 2. The 5 onsite formats (the pool)

### Format 1: Decomposition (the signature round)

**Length:** 60 min, no code required (or very little).

**The format:** open-ended prompt, often built around an individual or organization with a practical need. Round splits into (a) ideation — break the challenge into pieces and agree on approach, and (b) execution — sketch a high-level design with data + APIs.

**The Palantir-specific framing:** system design centered on **logic and data** rather than infrastructure depth. "Think of it as system design centered on logic and data rather than infrastructure depth."

**What they test:**

1. **Structured breakdown** — how methodically you split an ambiguous challenge into testable parts
2. **End-user empathy** — whether your solution stays anchored to the person or organization it serves
3. **Data reasoning** — define the schema, data sources, and APIs the solution needs
4. **Scoping judgment** — how realistically you size a solution against a tight delivery timeline
5. **Iteration** — whether you propose concrete ways to improve the first-cut solution

**The 5 sample questions (from real Palantir candidates):**

1. "Design a system to improve traffic in NYC."
2. "Design a sync system between two employee record systems."
3. "Design a system that lets multiple teams query a shared dataset without exposing the underlying raw data."
4. "Design an application to catalog and log species while exploring an unfamiliar environment."
5. "Given a dataset of taxi trips with fields like fare, locations, times, and distance, propose a solution that helps drivers and could ship within a week."
6. "Design a system to help a delivery driver decide which food orders to pick up, then extend it to how the platform assigns orders at scale."
7. "Break down a logistics or operations challenge into components, then define the APIs and data each piece needs."

**The opening line the guide recommends:** "Lead with clarifying questions about the data and the end-user before proposing anything. State your assumptions out loud, agree on scope with your interviewer, then move from ideation to a high-level design."

**The Phase 6 prep:** This is `../decomposition/README.md` (the 4-step framework: Clarify → Decompose → Design → Tradeoffs). Palantir's decomposition is exactly the framework applied to real-world, end-user-anchored prompts.

### Format 2: Learning (the speed-of-comprehension round)

**Length:** 60 min, paired with decomposition (often back-to-back on the same day).

**The format:** introduced to a new concept, library, or codebase you haven't seen before, usually with documentation provided. Asked to understand it and modify or extend the code across a few short stages. Choose your language from Python, Java, or TypeScript.

**What they test:**

1. **Learning agility** — how quickly you absorb an unfamiliar concept or API
2. **Question-led navigation** — whether you ask enough to stay aligned with the interviewer's intent
3. **Code comprehension** — your ability to read existing modules and understand how they fit together
4. **Implementation under ambiguity** — how you extend or modify code when the spec isn't fully defined

**The 3 sample questions:**

1. "Walk through the architecture of an unfamiliar application across several short stages, discussing its limitations and rearchitecting or fixing functions as you go."
2. "Work with a custom package-installer concept that pulls from multiple repositories using multithreading, then implement functions with a concurrency library."
3. "Read a set of provided modules and enhance them using a documented library in your chosen language."

**The opening line the guide recommends:** "Treat documentation from your interviewer as your map, and keep your questions high-level and purposeful, since too many low-level ones can read as needing hand-holding. Narrate what you understand so the interviewer can correct your mental model before you commit to an approach."

**The Phase 6 prep:** This is `../practical-coding/02-extend-codebase.md` (the "extend a codebase" sub-round). Palantir's learning round is brownfield-only; you will never see your own code.

### Format 3: Coding (the technical foundation round)

**Length:** 60 min in CodePair, ~15-20 min of embedded behavioral.

**The format:** standard data structures and algorithms with end-user framing. Expect an under-defined prompt; clarify scope, solve the core challenge, discuss how your approach affects the larger system.

**What they test:**

1. **Technical foundation** — data structures and algorithms applied cleanly
2. **Code quality** — readability, well-structured, naming, modularity
3. **Complexity awareness** — time and space trade-offs
4. **User-centric thinking** — weigh the end-user impact of your implementation choices

**The 3 sample questions:**

1. "Solve a hash map or string manipulation challenge tied to a product scenario."
2. "Implement a feature, then refactor it for readability and reuse."
3. "Extend your solution to handle a new requirement an end-user might request."

**The Phase 6 prep:** This is `../swe-coding/README.md` (the 8 patterns: arrays / hash tables / strings / trees / graphs / DP / recursion / linked lists) + `../practical-coding/README.md` (the AI-as-typing-accelerator pattern, but **note: AI is prohibited at Palantir** — use the patterns without the AI tool).

### Format 4: Re-engineering (the debugging round)

**Length:** 60 min in CodePair.

**The format:** hands you a block of unfamiliar code (several hundred lines, may include deliberate distractions), tells you how it should behave, gives you 60 min to find and fix what's broken.

**What they test:**

1. **Systematic debugging** — work through the code methodically instead of fixating on the first anomaly
2. **Comprehension speed** — quickly understand what unfamiliar code is meant to do
3. **Attention to detail** — separate real defects from red herrings
4. **Verification** — confirm a fix actually resolves the intended behavior

**The 3 sample questions:**

1. "Find and fix a double-counting bug in a function that tallies values in a HashMap."
2. "Debug a program that models infection spread across a social graph and returns the wrong count."
3. "Work through a short module first, then a longer one of several hundred lines, isolating the logic flaw in each."

**The opening line the guide recommends:** "Resist patching the first thing that looks wrong. Map how the code is supposed to work, then trace the output backward to isolate the defect."

**The Phase 6 prep:** This is `../practical-coding/03-debug.md` (the debug sub-round). Palantir's re-engineering round is the AI-prohibited version of the same format.

### Format 5: System design (the architecture round)

**Length:** 60 min on the CodePair whiteboard.

**The format:** industry-standard system design with Palantir's user-centric lens layered on top. Prompts often center on data pipelines and how raw, messy data becomes something usable.

**What they test:**

1. **Architecture clarity** — cleanly structure components and define responsibilities
2. **Trade-off defense** — reasoning for choices around databases, scaling, reliability
3. **Requirements gathering** — clarify scope and constraints before designing
4. **End-user orientation** — design decisions map to real usage and client needs

**The 3 sample questions:**

1. "Architect the components, data flow, and APIs for a real-world operational challenge, then walk through the trade-offs."
2. "Design a pipeline that ingests terabytes of sensor data in mixed formats like JSON, CSV, and XML, then surfaces failure predictions to a non-technical end-user."
3. "Design a system that lets multiple teams query a shared dataset without exposing the underlying raw data." (Same as decomposition Q3 — the same prompt can be a decomposition OR a system design round depending on which you draw.)

**The Phase 6 prep:** This is `../system-design/README.md` (the 9 patterns). Palantir's system design emphasizes the data pipeline patterns (#2 event-driven, #4 distributed storage, #6 batch) over the QPS/latency patterns.

---

## 3. The recruiter call (the 4 things they look for)

| # | Signal | What they test |
|---|---|---|
| 1 | Genuine motivation | Reasons for joining go beyond compensation or prestige |
| 2 | Mission alignment | Interests map to Palantir's government + commercial deployments |
| 3 | Long-term fit | Signs of staying and growing, not "stepping stone" |
| 4 | Project self-awareness | How clearly you reflect on what you've enjoyed and struggled with |

**The Palantir-specific signal:** "Palantir rejects technically strong candidates here when their motivation reads as generic, so come ready to connect your interest to Palantir's mission and products with specifics. Surface-level enthusiasm about interesting challenges won't carry the round."

**The 2 sample questions:**

1. "What are you looking for in your next role, and what do you want to work on?"
2. "Why Palantir, and what specifically draws you to the mission?"
3. "Walk me through your favorite and least favorite projects from past work."

**The Phase 6 prep:** This is `../interview-process.md` (the FDE loop, day-in-the-life) + `../behavioral/README.md` (the 3 question types: customer interaction, disagreement, ambiguity). The "Why Palantir" question is the canonical "company-specific" question that requires research on Gotham (government) or Foundry (commercial) + the operational challenges you'd want to own.

---

## 4. The hiring manager round (the 4 things they look for)

| # | Signal | What they test |
|---|---|---|
| 1 | Resolved doubts | Whether you close the gap on whatever the onsite panel flagged as weaker |
| 2 | Depth of ownership | How specifically you can speak to the metrics and trade-offs behind your past work |
| 3 | Self-reflection | How openly you discuss failures and what you took from them |
| 4 | Mission conviction | Whether your reasons for joining Palantir and this team hold up under follow-up |

**The candidate's framing (per the guide):** "The hiring manager interview is a 60-minute final round that revisits a weaker area from your onsite and carries the final hiring decision. It happens after the interview panel meets to discuss your onsite performance, and it's also where team matching tends to happen."

**The 4 sample questions:**

1. "Why Palantir, and why this team?"
2. "Tell me about a time you pushed back on a customer request."
3. "Tell me about your biggest failure."
4. "Walk me through the specific metrics and trade-offs from a project you owned."

**The opening line the guide recommends:** "Ask your recruiter which area the panel wants to revisit so you can prepare with focus. Treat questions about past failures as a test of self-awareness, and answer with a specific example and what you changed afterward."

**The Phase 6 prep:** This is `../behavioral/README.md` (the 3 question types + the 5-question cheat sheet mapped to Phase 1-5 case studies) + `../project-deep-dives/README.md` (the 45-min presentation, because the HM will dig into specific metrics + trade-offs).

---

## 5. What did they test? (the consolidated signals)

### The 7 signals (across all 4 stages)

1. **"Breaking a vague, real-world challenge into parts you can actually build."** → Decomposition. The FDE signal.
2. **"How fast you can understand an unfamiliar system and extend it."** → Learning. The Palantir-specific signal.
3. **"End-user framing: how you connect a technical solution to the person who'd use it."** → Customer-facing. The FDE signal.
4. **"Whether you ask questions to resolve ambiguity before writing code."** → Clarifying instincts. The decomposition signal.
5. **"How you connect your interest to Palantir's mission and products with specifics."** → Mission alignment. The recruiter-call signal.
6. **"How you weigh the end-user impact of your implementation choices."** → User-centric thinking. The coding signal.
7. **"Whether your debugging process is systematic rather than how fast you spot the first issue."** → Systematic debugging. The re-engineering signal.

### The 4 anti-patterns (per the guide)

1. **"Generic enthusiasm about interesting challenges."** The recruiter-call signal: surface-level enthusiasm is rejected. Specifics (the product, the mission, the operational challenge) are required.
2. **"Too many low-level questions."** The learning-round signal: high-level purposeful questions show you're leading; low-level questions read as needing hand-holding.
3. **"Patching the first thing that looks wrong."** The re-engineering signal: the obvious bug isn't always the real one. Trace the output backward.
4. **"Memorized patterns."** The learning-round signal: "memorized patterns won't carry it." Reading unfamiliar code fast + extending it is the test.

---

## 6. What's the Phase 6 module that preps each stage?

| Stage | Phase 6 module |
|---|---|
| 1. Recruiter call | `../interview-process.md` (the FDE loop, day-in-the-life) + `../behavioral/README.md` (the 3 question types) |
| 2. Technical screen | `../practical-coding/README.md` (the 3 sub-rounds) + `../swe-coding/README.md` (the 8 patterns) — **without the AI tool, since Palantir prohibits it** |
| 3a. Decomposition | `../decomposition/README.md` (the 4-step framework) |
| 3b. Learning | `../practical-coding/02-extend-codebase.md` (the extend-a-codebase sub-round) |
| 3c. Coding | `../swe-coding/README.md` + `../practical-coding/README.md` (without AI) |
| 3d. Re-engineering | `../practical-coding/03-debug.md` (the debug sub-round) |
| 3e. System design | `../system-design/README.md` (the 9 patterns) |
| 4. Hiring manager | `../behavioral/README.md` (the 3 question types) + `../project-deep-dives/README.md` (the 45-min presentation) |

**The candidate's pre-Phase-6 prep time would have been:** ~4 weeks full-time, weighted 30% on decomposition (the signature round) + 25% on learning (the speed-of-comprehension round) + 20% on system design + 15% on re-engineering + 10% on behavioral (the embedded questions).

---

## 7. The 5-pattern cheat sheet for Palantir FDE prep

Based on this guide + the Phase 1-5 portfolio:

1. **Practice decomposition out loud.** Take vague, real-world prompts and break them into components, data needs, and APIs while narrating your reasoning. **This is the single most distinctive skill the loop tests.**
2. **Build a learning workflow.** Practice reading unfamiliar code and documentation quickly, then extending it. The learning round tests comprehension speed and question-led navigation; **memorized patterns won't carry it.**
3. **Frame every solution around the end-user.** For each coding or design challenge, articulate who uses the result and how you'd improve their experience with caching, pre-computation, or cleaner interfaces.
4. **Prepare embedded behavioral answers.** Build structured behavioral responses you can deliver mid-technical-round, including a specific, well-researched account of why Palantir. **The 15-20 minutes of behavioral in every round is the differentiator.**
5. **Run full mock interviews.** Simulate the interview format with peer and AI mock interviews. **Prep all 5 onsite formats without knowing which 3 you'll get.**

---

## 8. The 5 most common Palantir FDE follow-up questions (inferred from this guide)

| Question | The FDE answer |
|---|---|
| 1. "Why Palantir?" | "I've spent the last 6 months building a customer-facing AI service for PacificFreight (a 12-person cross-border logistics SMB), and the work that resonates most is the same work Palantir does on Gotham and Foundry: turning operational data into tools that field teams use daily. The operational challenge I want to own is multi-tenant data isolation + the eval-set-as-spec pattern at scale. Palantir's FDSE role is the only one I've seen that lets me own the engineering build end-to-end with a customer in the room." (Per the guide: "Name the product you'd want to build on, Gotham for government deployments or Foundry for commercial ones, and the kind of operational challenge you want to own. Expect the question again in the hiring manager round with follow-ups, so your reason needs to hold up under detail.") |
| 2. "Design a system that lets multiple teams query a shared dataset without exposing the underlying raw data." | "4-step framework. Clarify: the user is a data analyst on a downstream team; the constraint is row-level access control + a query budget per team; the failure mode is a leak of PII; the timeline is MVP in 2 weeks. Decompose: shared dataset, query interface, ACL layer, audit log, per-team budget. Design: a SQL view layer over the warehouse with row-level security + a per-team rate limit (Redis token bucket) + an audit log (append-only). Tradeoffs: SQL view vs API gateway (we chose SQL for query power, accepted the per-team schema work); Postgres RLS vs application-layer ACL (we chose RLS for security correctness, accepted the migration cost). Data: warehouse tables + ACL table + audit log table. Cost: $200/month for 10 teams." |
| 3. "Walk me through the architecture of an unfamiliar application." | "I'd read the README first (1 min), then map the directory structure (1 min), then trace the request flow from the entrypoint through the middleware to the data layer (5 min). I'd ask the interviewer what the most uncertain piece is — that's where I'd spend my time. I'd narrate my mental model out loud so the interviewer can correct it before I commit to a fix." |
| 4. "Find and fix a double-counting bug in a HashMap." | "I wouldn't patch the first thing that looks wrong. I'd read the full function top to bottom, write down the expected output for 2-3 test cases, then trace the actual output. The bug is usually in the accumulator (add the same key twice, or initialize the count to 1 when it should be 0). I'd write a regression test that exercises the same input, run the test to confirm it fails, apply the fix, run the test to confirm it passes, and walk the interviewer through the before/after." |
| 5. "Tell me about your biggest failure." | "Engagement 2 of my FDE portfolio: I told a legal-tech customer their data wasn't RAG-ready and walked away after 2 weeks. I lost 2 weeks of work. The lesson: I should have run the data audit in week 1, not week 2. I now run a 'data-readiness check' as the first deliverable of every engagement — 30 rows of sample data, 4 quality metrics, a go/no-go decision before any prompt engineering. Better to lose 2 weeks than ship a system that fails at week 11." |

**Memorize these 5.** They're the most common Palantir FDE follow-ups based on this guide.

---

## 9. Palantir-specific prep tips (the 5 from the guide)

1. **"Practice decomposition out loud"** — take vague, real-world prompts and break them into components, data needs, and APIs while narrating your reasoning.
2. **"Build a learning workflow"** — practice reading unfamiliar code and documentation quickly, then extending it.
3. **"Frame every solution around the end-user"** — articulate who uses the result and how you'd improve their experience.
4. **"Prepare embedded behavioral answers"** — build structured behavioral responses you can deliver mid-technical-round.
5. **"Run full mock interviews"** — simulate the interview format with peer and AI mock interviews, or work with an expert coach for targeted feedback.

---

## 10. How to use this report

1. **Read it once.** Internalize the 4 stages + the 5 onsite formats + the consolidated signals.
2. **Prep all 5 formats.** The 3-round pool is drawn from a pool of 5; you don't know which 3 you'll get.
3. **Practice decomposition out loud.** This is the single most distinctive skill the loop tests.
4. **Build a learning workflow.** Reading unfamiliar code fast + extending it is the test.
5. **Frame every solution around the end-user.** "Who uses the result? How would you improve their experience?"
6. **Prepare for the "Why Palantir?" question.** Specifics (Gotham, Foundry, the operational challenge) are required.
7. **No AI tools.** Palantir prohibits them throughout.
8. **Bring a Phase 1-5 case study as your "real customer" example.** PacificFreight is the default.

---

## 11. Palantir compensation (FYI, for context)

**U.S. range:** $171K to $295K
**U.S. median:** ~$211K

Compensation combines base + equity + bonus. Packages vary by experience and location. (Source: Levels.fyi, per the guide.)

---

## 12. The thesis

Palantir invented the FDE loop. **If you can pass Palantir's loop, you can pass any FDE loop.** The 4 stages test the same 7 signals: decomposition, learning, end-user framing, clarifying instincts, mission alignment, user-centric thinking, systematic debugging. **The 3-round pool is the differentiator** — you need to prep all 5 formats without knowing which 3 you'll get. The 4-step framework (Clarify → Decompose → Design → Tradeoffs) is the structure; the end-user narrative is the content; the embedded behavioral is the surprise.

**General FDE prep gets you past the resume screen. Palantir-specific prep gets you past the decomposition round.**

---

## 13. FDSE vs deployment strategist (the two Paltanir FDE-adjacent roles)

Palantir hires under **two separate job families**, and the loops are not interchangeable:

| Role | Title | What they own | Loop difference |
|---|---|---|---|
| **Forward Deployed Software Engineer (FDSE)** | The engineering build on Gotham (government) or Foundry (commercial) | The full engineering build — problem framing, data work, front-end, back-end, AI/ML layer | This is the loop described above. Decomposition + 2 from the pool + behavioral embedded |
| **Deployment Strategist** | Sits closer to the customer's problem definition; less hands-on implementation | Translates ambiguous client needs into scoped work for the FDSEs to build | Pairs the decomposition round with a SQL-heavy technical round; shape varies by team and by recruitment channel |

**The 2 things to know if you're applying to one and not the other:**

1. **If you see "FDSE" in the title**, you're on the loop in this report. Plan for 60-min rounds in CodePair, the 3-of-5 pool, and AI prohibited throughout.
2. **If you see "Deployment Strategist" in the title**, plan for the same decomposition round + a separate SQL fluency round (joins, aggregations, business-question SQL on a provided schema). The SQL round is the differentiator; the FDSE loop barely tests SQL.

**The candidate's takeaway:** "Both center on the decomposition round, but the deployment strategist loop pairs it with a technical round built around SQL fluency, and its shape varies by team and by how you were recruited."

**The Phase 6 prep:** the SQL module (if present) for the deployment-strategist loop. This report is for the FDSE loop.

---

## 14. Experience requirements (and the security-clearance nuance)

Palantir hires FDEs **across experience levels**, from new graduates to senior engineers. The interview is the same; the bar is the same.

| Experience level | Expected signals | Onsite prep |
|---|---|---|
| New graduate | Strong technical foundation; clear motivation for FDE work; can do the decomposition round with prompting | Same 5 onsite formats, weighted 35% on decomposition + 25% on behavioral |
| Mid-level (3-7 years) | End-to-end ownership of past projects; can speak to metrics + trade-offs | Same 5 onsite formats, weighted 30% on decomposition + 20% on system design + 20% on re-engineering |
| Senior (7+ years) | Cross-functional leadership; can defend a system design under pushback | Same 5 onsite formats, weighted 25% on system design + 25% on decomposition + 25% on behavioral |

**The security-clearance nuance:** "Some government-facing forward deployed engineer roles require or sponsor a security clearance, while most commercial roles do not." If you see a Gotham (government) posting, the clearance requirement is a separate signal — start the clearance process early (it can take 6+ months).

**The cross-functional background note:** "Palantir welcomes candidates from non-traditional backgrounds who can demonstrate strong technical ability." The bar is on the loop, not the resume.

**The Phase 6 prep:** the same 4 weeks of full-time prep regardless of level. The portfolio (4 projects + 5 case studies) is the strongest signal you can bring for any level.
