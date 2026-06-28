# Sonar — Engineering Director — Interview Prep for Prem Vishnoi

> Built from your real CV. All STAR answers use your actual projects and metrics. Adjust wording to sound like you.

---

## ⚠️ Read This First: The Profile Gap (and how to win on it)

**The situation:** This Sonar JD is a *software* Engineering Director role — Java/JavaScript, leading squads building a code-verification platform. Your background is *Data/AI/ML* leadership. A sharp recruiter will ask about this.

**Don't hide it — reframe it.** Your bridge:
1. **You lead engineers at scale** — 30-person org, 4 squads, EMs reporting to you, $3M budget. That's exactly the management-of-managers scope they want.
2. **Sonar's product is about AI-generated code quality** — you've *delivered* GenAI/LLM systems end-to-end (Text-to-SQL, agentic AI, RAG). You understand the exact problem space their product solves: making AI output trustworthy.
3. **You ship production software** — Spark, Kafka, Flink, Java, Scala, CI/CD, distributed systems. You're not just a "data person"; you run real engineering orgs.

**Your one-liner for the gap:**
> "My core is data and AI, but at the Director level the job is the same: setting technical direction, growing engineering managers, and holding a high quality bar. And given Sonar's mission is verifying AI-generated code, my hands-on GenAI delivery experience means I deeply understand the problem your customers face — I've lived the 'is this AI output actually trustworthy?' question."

If the role genuinely requires deep Java/JS platform expertise day-to-day, be honest that's not your center of gravity — but make them see the leadership + AI-domain value.

---

## Your 60-Second Intro (use in Steps 1, 2, 5)

> "I'm Prem — a Data, Analytics and AI leader with 15+ years across retail, fintech, banking, and e-commerce in Southeast Asia. Right now I'm Head of Data Engineering at Makro, part of CP Group, where I lead a 30-person org across Data Engineering, Analytics, BI and AI for an $8 billion omnichannel business in 3 countries, owning architecture, a $3M budget, and AI strategy. Before that I was VP of Data Engineering at Lazada — Alibaba — where I earned a double promotion building their real-time data platform. I'm a hands-on leader: I've personally owned AI/ML and GenAI products from problem framing to production. I'm drawn to Sonar because making AI-generated code trustworthy is exactly the kind of problem I've been working on from the data and AI side."

---

# STEP 1 — Recruiter Interview (15–30 min)

### Q: "Tell me about yourself." → Use the 60-sec intro above.

### Q: "Why Sonar?"
> "Two reasons. First, the mission — AI is writing more and more production code, and verifying it's reliable and secure is becoming critical. I've delivered GenAI systems myself, so I know firsthand you can't just trust the output; you need independent verification. That's exactly Sonar's bet. Second, the role — I want to keep leading engineering at scale, growing managers and setting technical direction, at a company where quality is the product, not an afterthought."

### Q: "Why are you leaving Makro / looking now?"
> "I've built and scaled the data org from 8 to 30 and modernised the whole platform — it's in a strong place. I'm looking for the next challenge where I can apply that leadership at a company at the frontier of AI, and Sonar's mission fits that precisely."

### Q: "This role is Java/JavaScript software engineering — your background is data/AI. Talk to me about that."
> Use the gap reframe above. Lead with leadership scope + AI-domain relevance. Be confident, not defensive.

### Q: Logistics
- **Location:** "I'm based in Singapore — Vietnam TRC holder, and fully open to Singapore." ✅ (You meet the hard requirement — say it clearly.)
- **Notice period:** [your real notice — fill in].
- **Comp:** "Based on Director-level engineering comp in Singapore, I'm targeting [range]. I'm flexible on the overall package."
- **Other processes:** Honest but brief.

### ✅ Your questions:
1. "How is the Singapore engineering org positioned vs. other hubs — building independent product lines?"
2. "What does success look like for this Director in the first 90 days?"
3. "How does Sonar weigh leadership and domain experience vs. deep Java/JS background for this role?" *(smart — surfaces the gap on your terms)*

---

# STEP 2 — First Technical Video Interview (30–90 min)

> You may be asked to write simple code in a shared editor. Your strongest languages are **Python and SQL** (also Java/Scala). Brush up on a few easy/medium problems. Think out loud, clarify first.

### Q: "Walk me through something you built — an achievement and a struggle."
**Your best story — Makro Lakehouse + financial close:**
> **S:** "At Makro, finance was closing the books manually over 5 days, and legacy systems couldn't handle the data volume." **T:** "I owned the enterprise data strategy and modernisation." **A:** "I led the migration to a Databricks Lakehouse processing 10B+ rows daily, and built the analytics foundation on top." **R:** "Month-end close dropped from 5 days to 2 hours, and we delivered 50+ executive dashboards. The struggle was change management — getting finance to trust automated numbers — which I solved by running parallel reconciliation until they had confidence."

### Q: "Walk through identifying an issue, solving it, and measuring impact."
**Lazada real-time platform:**
> **S:** "Lazada's logistics needed real-time visibility but the platform couldn't scale." **T:** "I architected a real-time data platform." **A:** "Built it on Kafka, Flink, ClickHouse and HBase, processing 100M+ daily events." **R:** "It generated 20M+ daily insights and improved delivery routing and SLAs. Earned a double promotion for the impact."

### Q: "How do you ensure quality — especially with AI-generated code?" 🔑 *(Sonar's core — nail this)*
> "I've delivered GenAI systems in production — a Text-to-SQL platform where business users query data in natural language. The hard part wasn't generating SQL; it was *guardrails* — making sure the AI output was correct and safe before it touched real data. I built schema understanding, a semantic layer, prompt guardrails, and validation. That's the same problem Sonar solves at code scale: AI output looks plausible but needs independent verification. I'm a strong believer that as AI writes more code, automated quality gates and verification in the pipeline stop being optional."

### Q: "How do you work with stakeholders / cross-functional teams?"
**Dynamic Pricing story:**
> "For the dynamic pricing model at Makro, I framed the problem *with* the commercial team, did feature engineering on transactional and competitor data, built a gradient-boosting model, deployed on Databricks, and drove adoption with merchandising. The win was as much stakeholder alignment as ML — getting merchandisers to trust and act on the model's pricing."

### Q: "Tech debt vs delivery?"
> "At Makro I set KPIs tied to business outcomes, not just engineering output, and protected capacity for platform/foundation work — that's why we could expand into new countries fast using reusable architecture. Debt that risks reliability gets prioritised; the rest is planned, visible work."

---

# STEP 3 — TestGorilla Culture Fit (10–25 min, online)

- Be honest and consistent — don't game it.
- Your natural strengths map well to Sonar's **CODE** values: quality-obsession (you set outcome-based KPIs), customer focus, deliberate decisions, teamwork.
- Favor answers showing ownership, data-driven decisions, direct communication, collaboration over solo heroics.

---

# STEP 4 — Technical Assessment (1–2 hr)

> Realistic use case + present it. Be strategic — frame solutions around how they fit Sonar (code quality, scale, multi-tenancy, developer experience).

**Your edge:** You design enterprise platforms for a living. If given a system-design case:
- Lead with **scale/architecture** (your strength): ingestion → processing → storage → serving, like your Lakehouse and real-time platforms.
- Add the **Director lens**: how you'd staff/structure teams, measure success (DORA + defect rates), build-vs-buy.
- Reference real analogues: "I designed something similar at Lazada — 600+ governed tables, 10x data growth, real-time at 100M events/day."

**If it leans pure Java/JS coding:** prepare honestly. Practice the language they emphasize. Lean on your problem-solving narration and system thinking even if syntax is rusty.

---

# STEP 5 — Cross-Functional Interview (30 min)

*A leader from another division. Explain simply, show collaboration.*

### Listed questions:

**"Introduction about yourself."** → 60-sec intro, lighter on tech.

**"Why do you want to join Sonar?"** → Mission + AI-quality angle.

**"How do you project yourself at Sonar?"**
> "Leading the Singapore engineering org, growing my engineering managers into stronger leaders, raising the delivery and quality bar, and over time contributing to broader technical strategy across hubs. I've scaled a team from 8 to 30 before — I'd bring that same org-building focus here."

**"Example of a challenging time."**
**SCB AML story** (good for a non-eng audience — it's about risk/compliance):
> "At Standard Chartered I built AML compliance pipelines across 15+ countries. The challenge was false positives — investigators were drowning in alerts. I built fuzzy-matching and entity-resolution algorithms in the Lucid Search app that materially cut false positives and investigation time. Hard because it spanned multilingual records, regulatory scrutiny (MAS), and many stakeholders — pure technical skill wasn't enough; it needed cross-team trust."

### Tips: explain in layman's terms (no jargon dumps), emphasize collaboration. You scaled teams, managed vendors, aligned execs — use those.

---

# STEP 6 — Leadership Interview (20–30 min, often CEO)

*Vision & culture fit. 2-way. Not salary. Your last chance to dig deep.*

**Q: "Where is the industry going?"**
> "AI agents are writing a growing share of production code. That shifts the bottleneck from *writing* code to *trusting* it — verification, security, maintainability at scale. The winners will make AI-generated code trustworthy. I've seen this from the data/AI side — building GenAI systems where the output is only useful if you can verify it. Sonar is solving exactly that, at code scale. That's why I'm excited."

**Q: "What kind of leader are you?"**
> "Hands-on but delegating. I set clear technical direction, grow my managers into leaders, and tie KPIs to business outcomes, not vanity engineering metrics. I scaled Makro's data org from 8 to 30 and earned a double promotion at Lazada for cross-functional impact — both came from raising the bar and developing people, not doing it all myself."

**Q: "What would you achieve here in 1-2 years?"**
> "Build a high-performing Singapore engineering org, develop strong EMs, raise the quality and delivery bar, and have the team contribute meaningfully to Sonar's flagship products — bringing my AI-delivery perspective to a product that's all about trustworthy AI code."

### ✅ Questions for the CEO:
1. "What's Sonar's biggest bet over the next 2-3 years, and where does engineering fit?"
2. "As you scale, how do you keep the human-sized culture you describe?"
3. "How do Sonar's own teams use AI coding agents internally — and verify that code?"

---

# Your Master Checklist

**Your STAR stories (all from your CV — ready to go):**
- [ ] Makro Lakehouse + 5-days-to-2-hours close (achievement / scale / change mgmt)
- [ ] Lazada real-time platform, 100M events/day + double promotion (impact)
- [ ] Text-to-SQL GenAI + guardrails (AI quality — Sonar's core)
- [ ] Dynamic pricing model (stakeholder/cross-functional)
- [ ] SCB AML / false positives (challenging time)
- [ ] Scaling org 8→30 across 4 squads (management-of-managers)

**Technical refresh:**
- [ ] A few easy/medium coding problems (Python or whichever they request)
- [ ] DORA metrics
- [ ] One system-design you can sketch (lean on your Lakehouse/real-time work)
- [ ] Honest, confident framing of the data/AI → software-eng gap

**Company knowledge:**
- [ ] Products: SonarQube, Foundation Agent, SonarSweep, Context Augmentation
- [ ] CODE values + AC/DC concept

**Logistics decided:**
- [ ] Comp range
- [ ] Notice period (Singapore location ✅ already strong)
- [ ] Questions ready per round

**Setup:** internet, headset, webcam, quiet room, test Zoom/Meet.
