# Sonar — Engineering Director — 5 Q&A Per Round (Prem Vishnoi)

> Answers built from your real CV. Speak them naturally — don't memorize word-for-word. **[brackets]** = fill in your number.

**Your 60-sec intro (reuse everywhere):**
> "I'm Prem — a Data, Analytics and AI leader with 15+ years across retail, fintech, banking and e-commerce in Southeast Asia. Currently Head of Data Engineering at Makro, CP Group, leading a 30-person org across Data Engineering, Analytics, BI and AI for an $8B omnichannel business in 3 countries — owning architecture, a $3M budget, and AI strategy. Before that, VP of Data Engineering at Lazada (Alibaba), where I earned a double promotion building their real-time platform. I'm hands-on — I've owned AI/ML and GenAI products end to end. Sonar draws me because making AI-generated code trustworthy is exactly the problem I've worked on from the data and AI side."

---

# ROUND 1 — Recruiter Interview (15–30 min)

**Q1. Tell me about yourself.**
> [Use the 60-sec intro above.]

**Q2. Why do you want to join Sonar?**
> "Two reasons. The mission first — AI is writing more production code every day, and verifying it's reliable and secure is becoming critical. I've built GenAI systems myself, so I know you can't blindly trust AI output; you need independent verification. That's Sonar's core bet. Second, the role — I want to keep leading engineering at scale, growing managers and setting technical direction, at a company where quality *is* the product."

**Q3. Your background is Data/AI, but this is a software engineering (Java/JS) Director role. How do you see the fit?**
> "At Director level the job is the same regardless of stack: set technical direction, grow engineering managers, hold a high quality bar, and align with the business. I do that today across a 30-person org and four squads. What I add on top is domain relevance — Sonar's product is about trustworthy AI-generated code, and I've delivered exactly that kind of system, with guardrails and verification. I understand your customers' problem because I've lived it."

**Q4. What's your notice period, location, and salary expectation?**
> "I'm based in Singapore and fully eligible to work here, so location is no issue. Notice period is [X weeks]. On comp, based on Director-level engineering roles in Singapore I'm targeting [range], and I'm flexible on the overall package — base, equity, and benefits together."

**Q5. Why are you leaving your current role at Makro?**
> "I've taken the data org from 8 to 30 people and modernised the whole platform — it's in a strong, stable place now. I'm looking for the next challenge where I can apply that leadership at a company at the frontier of AI. Sonar fits that precisely."

---

# ROUND 2 — First Technical Video Interview (30–90 min)

**Q1. Walk me through a project you're proud of — an achievement and a struggle.**
> "At Makro, finance was closing the books manually over 5 days on legacy systems that couldn't handle the volume. I owned the modernisation — migrated to a Databricks Lakehouse processing 10B+ rows daily, and built the analytics layer on top. Month-end close dropped from 5 days to 2 hours, with 50+ executive dashboards. The struggle was trust — finance didn't believe automated numbers at first. I ran parallel reconciliation until they had full confidence, then cut over."

**Q2. Describe a time you identified an issue, built a solution, and measured the impact.**
> "At Lazada, logistics needed real-time visibility but the platform couldn't scale. I architected a real-time data platform on Kafka, Flink, ClickHouse and HBase processing 100M+ events daily. It produced 20M+ daily insights and measurably improved delivery routing and SLAs. The impact was significant enough that I earned a double promotion for it."

**Q3. How do you ensure code/output quality — especially with AI-generated content?** 🔑
> "I delivered a Text-to-SQL GenAI platform letting business users query enterprise data in natural language. The hard part wasn't generating SQL — it was guardrails: making sure AI output was correct and safe before it touched production data. I built schema understanding, a semantic layer, prompt guardrails and validation. That's the same shape as Sonar's problem at code scale — AI output looks plausible but needs independent verification. As AI writes more code, automated quality gates stop being optional."

**Q4. How do you handle technical debt versus delivery pressure?**
> "I make debt visible and planned, not invisible. At Makro I set KPIs tied to business outcomes, not just engineering output, and protected capacity for foundational work — which is exactly why we could expand into new countries fast using reusable architecture and templates. Debt that threatens reliability jumps the queue; the rest is scheduled, tracked work on the roadmap."

**Q5. How do you collaborate with product, data science, and other stakeholders?**
> "For Makro's dynamic pricing model, I framed the problem *with* the commercial team, engineered features from transactional and competitor data, built a gradient-boosting model, deployed on Databricks, and drove adoption with merchandising. The technical model was half the work — the other half was stakeholder trust, getting merchandisers to actually act on the model's recommendations. I treat cross-functional alignment as part of engineering, not separate from it."

---

# ROUND 3 — TestGorilla Culture Fit (10–25 min, online assessment)

> This is a behavioral assessment, not a live interview — but here's the mindset and how you'd answer the typical situational prompts.

**Q1. When you disagree with a teammate's technical approach, what do you do?**
> Choose answers showing: you raise it directly and with data, seek to understand their view, and once a decision is made you commit. (Maps to Sonar's "Deliberate" + "Effective as one team.")

**Q2. How do you prefer to make decisions — fast and intuitive, or deliberate and data-driven?**
> Favor deliberate + data-driven, while noting you can move fast when needed. Stay consistent with how you've described yourself elsewhere — these tests flag contradictions.

**Q3. What motivates you most at work?**
> Building things with measurable business impact and growing people. (Backed by your real record — scaling 8→30, outcome-based KPIs.)

**Q4. How do you respond when a project fails or misses its goal?**
> Take ownership, run a blameless analysis, extract the lesson, adjust. Avoid blame-shifting answers.

**Q5. Do you prefer working independently or collaboratively?**
> Collaborative leadership — you set direction and grow managers rather than doing everything yourself.

**Rule for this round:** Be honest and consistent. Don't try to "pass" — answer as the leader you actually are. Your real profile already aligns with Sonar's quality-obsessed, customer-focused culture.

---

# ROUND 4 — Technical Assessment (1–2 hr, use case)

**Q1. Design a scalable system to process and analyze code/data from thousands of sources with low latency.**
> "I'd go event-driven: ingest on commit/PR via webhooks into a queue, then horizontally-scalable workers do the analysis — incrementally, only re-processing changed files to control latency and cost. Results land in a store with an API and dashboard on top. I've built this shape before — at Lazada, 100M+ events/day on Kafka/Flink; at Makro, 10B+ rows/day on a Lakehouse. Key tradeoffs: latency vs cost, false-positive tuning, and multi-tenant isolation."

**Q2. How would you staff and structure the team to build and run this?**
> "Squad-based by domain, each with an EM I grow and hold accountable — that's how I run Makro today across Finance, Supply Chain, O2O and Platform. A dedicated platform squad owns shared infrastructure and quality gates so feature squads move fast on a stable foundation."

**Q3. How would you measure whether this system and team are succeeding?**
> "DORA metrics for delivery — deploy frequency, lead time, change failure rate, MTTR — plus outcome metrics: defect/regression rate, and business impact. I deliberately tie KPIs to business outcomes, not vanity engineering numbers."

**Q4. Walk us through your reasoning and where you'd push back on the prompt.**
> Narrate assumptions out loud, ask clarifying questions about scale/constraints, and name alternatives you considered before committing. They explicitly want to see you *challenge* the prompt, not silently accept it.

**Q5. What would you do differently with more time/resources?**
> Always have a "next iteration" answer — e.g., add monitoring/retraining for any ML component (like you industrialised models at Lazada with monitoring, retraining, governance), or harden multi-tenancy and observability.

**Strategy:** Frame everything around how it fits Sonar — quality, scale, developer experience. Lean on your enterprise-platform strength; that's your edge here.

---

# ROUND 5 — Cross-Functional Interview (30 min, leader from another division)

> They may not be technical — explain simply, emphasize collaboration. These 4 are the questions Sonar's guide explicitly lists, plus one likely.

**Q1. Introduction about yourself.**
> [60-sec intro, lighter on jargon. Emphasize impact and people, not architecture details.]

**Q2. Why do you want to join Sonar?**
> "I like that engineering, product, and customer-facing teams here are all aligned around one mission — trustworthy code. I've spent my career making data and AI outputs reliable enough for the business to act on, so the mission resonates, and I want to lead engineering at that frontier."

**Q3. How do you project yourself at Sonar?**
> "Leading the Singapore engineering org, growing my managers into stronger leaders, raising the delivery and quality bar, and over time contributing to broader technical strategy across hubs. I've scaled a team from 8 to 30 before — I'd bring that same org-building focus here."

**Q4. Tell me about a challenging time.**
> "At Standard Chartered I built AML compliance pipelines across 15+ countries. Investigators were overwhelmed by false-positive alerts. I built fuzzy-matching and entity-resolution algorithms in our Lucid Search app that materially cut false positives and investigation time. It was hard because it spanned multilingual records, MAS regulatory scrutiny, and many stakeholders — pure technical skill wasn't enough; it took cross-team trust and clear communication."

**Q5. Give an example of working well across functions outside engineering.**
> "Across every role I've managed vendors, owned budgets, and aligned executives. At Makro I work daily with commercial, finance, and marketing — for example the MarTech automation project combined customer segmentation, propensity scoring and GenAI insights, which only worked because marketing and I co-designed it. I see engineering as a partner to the business, not a service desk."

---

# ROUND 6 — Leadership Interview (20–30 min, often CEO)

> Vision & culture fit. A 2-way conversation. NOT salary. Your last chance to dig deep and show conviction.

**Q1. Where do you see the industry / AI in software going?**
> "AI agents are writing a growing share of production code, which shifts the bottleneck from *writing* code to *trusting* it — verification, security, maintainability at scale. The winners will be whoever makes AI-generated code trustworthy. I've seen this from the data and AI side, building GenAI systems whose output is only useful if you can verify it. Sonar is solving exactly that, at code scale — which is why I'm genuinely excited about it."

**Q2. What kind of leader are you?**
> "Hands-on but delegating. I set clear technical direction, grow my managers into leaders, and tie KPIs to business outcomes rather than vanity metrics. Scaling Makro's org from 8 to 30 and earning a double promotion at Lazada both came from raising the bar and developing people — not from doing everything myself."

**Q3. What would you want to achieve at Sonar in your first 1-2 years?**
> "Build a high-performing Singapore engineering org, develop strong EMs, raise the quality and delivery bar, and have the team contribute meaningfully to your flagship products — bringing an AI-delivery perspective to a product that's all about trustworthy AI code."

**Q4. What concerns or questions do you have about Sonar?**
> Be genuine — this is a 2-way street. Good ones: *"What's the biggest bet Sonar is making over the next 2-3 years, and where does engineering fit?"* and *"As you scale, how do you protect the human-sized culture you describe?"*

**Q5. Why should we hire you over a candidate with a deeper Java/JS background?**
> "Because at this level you're hiring a leader, not a senior IC. I bring proven management-of-managers at scale, a track record of shipping under real business pressure, and — uniquely — deep hands-on experience with the exact AI-trustworthiness problem your product solves. A stronger Java engineer can't necessarily grow your managers, scale your org across countries, or speak credibly to your customers about why AI-generated code needs verification. I can."

---

## Final reminders
- **Singapore location is a strength** — state it clearly and early.
- **Own the data/AI → software gap** — reframe as leadership + domain relevance, never apologize for it.
- **Rounds 2 & 4 may include live coding** — brush up a few problems in the language they specify.
- **Have your numbers ready:** 8→30 org, $3M budget, $8B business, 10B+ rows/day, 100M+ events/day, 5 days→2 hours, double promotion.
