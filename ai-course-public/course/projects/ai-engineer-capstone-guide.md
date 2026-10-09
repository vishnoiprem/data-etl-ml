# AI Engineer Mastery — Capstone Project Guide
**Build & ship your own AI SaaS in 8 weeks**

---

## What is the Capstone?

The capstone is the final project of the AI Engineer Mastery course. It's a real, deployed AI product that:

- Solves a real problem for real users
- Uses at least 3 of the techniques taught in the course (LLM APIs, RAG, agents, etc.)
- Is deployed to production (not just running on localhost)
- Has at least 10 paying or active users
- Is publicly documented (GitHub, blog post, demo video)

This is the project that goes on your portfolio. It's what shows in interviews. It's what gets you hired or funded.

---

## How it works

1. **Week 1-2: Pick your idea** (use the framework below)
2. **Week 3-4: Build the MVP** (focus on core feature, no polish)
3. **Week 5-6: Get first users** (launch, iterate, get feedback)
4. **Week 7-8: Polish & document** (landing page, blog post, video walkthrough)
5. **Week 8: Demo Day** (live demo to the cohort + instructors)

Cohort students get weekly code reviews. Premium students get 1:1 mentoring on their capstone.

---

## Picking your idea — The IDEAL framework

Use this to validate your idea before building:

### I — Interesting to YOU
You'll spend 200+ hours on this. Pick something you actually care about. Don't build "another AI wrapper" because Twitter said it would make money. Build something you'd use yourself.

### D — Demonstrable
Can you show it working in a 2-minute demo? If it requires 10 minutes of explanation, it's too complex. Aim for "see, type, magic happens."

### E — Easy to explain
Can you explain it in one sentence? "It's [X] for [Y] that does [Z]." If you need a paragraph, simplify.

### A — Audience exists
Are there 1,000+ people who would pay for this? Not just "use it" — pay. $5/mo or $50 one-time. Find the audience on Reddit, Twitter, Discord, or LinkedIn BEFORE you build.

### L — Leverage your skills
Use what you already know. If you're a doctor, build for doctors. If you're a lawyer, build for lawyers. Domain knowledge = competitive moat.

**If your idea passes all 5, build it.**

---

## 5 Capstone Templates (pick one or invent your own)

### Template 1: AI Document Q&A
**What:** Upload PDFs and ask questions about them
**Audience:** Lawyers, researchers, analysts, students
**Monetization:** $19/mo per user
**Tech stack:** RAG + Pinecone + FastAPI + Stripe
**Why this works:** Universal need, clear value, easy to demo

**MVP features:**
- Upload PDF
- Auto-chunk and embed
- Search bar for questions
- Answers with citations to source pages
- Multi-document support
- Save search history

**Stretch goals:**
- OCR for scanned PDFs
- Multi-language support
- Team workspaces
- Slack/Notion integrations

---

### Template 2: AI Research Assistant
**What:** Agent that does multi-source research and writes reports
**Audience:** Consultants, investors, students, journalists
**Monetization:** $49/mo per user
**Tech stack:** ReAct agent + Tavily + GPT-4o + LangGraph
**Why this works:** Research is expensive and time-consuming

**MVP features:**
- Input: research question
- Agent searches 10+ sources
- Synthesizes findings into a report
- Cites all sources
- Saves reports to user dashboard

**Stretch goals:**
- Custom research templates
- PDF export
- Team collaboration
- Industry-specific research (medical, legal, etc.)

---

### Template 3: AI Sales Coach
**What:** Practice sales calls with an AI that gives feedback
**Audience:** Sales teams, founders, SDRs
**Monetization:** $99/mo per user
**Tech stack:** Whisper + GPT-4o + function calling + RAG
**Why this works:** Sales coaching is expensive ($200+/hr)

**MVP features:**
- Record a mock sales call
- AI analyzes tone, pace, objections
- Suggests improvements
- Tracks progress over time
- Compares to top performers

**Stretch goals:**
- Real-time call coaching
- Team leaderboards
- Custom playbooks per industry
- CRM integrations

---

### Template 4: AI Data Analyst
**What:** Upload CSV and ask questions in natural language
**Audience:** Analysts, marketers, ops teams
**Monetization:** $29/mo per user
**Tech stack:** Code interpreter + GPT-4o + Pandas + Plotly
**Why this works:** Not everyone knows SQL or Python

**MVP features:**
- Upload CSV (up to 100MB)
- Ask questions in plain English
- Auto-generates charts
- Exports insights to PDF
- Saved queries

**Stretch goals:**
- Multi-file analysis
- Database connections (Postgres, MySQL)
- Scheduled reports
- Team workspaces

---

### Template 5: AI Content Generator
**What:** Generate SEO-optimized blog posts from a topic
**Audience:** Marketers, agencies, indie hackers
**Monetization:** $39/mo per user
**Tech stack:** GPT-4o + web search (Tavily) + RAG
**Why this works:** Content is the #1 marketing need

**MVP features:**
- Input: topic + target keyword
- AI researches top 10 SERP results
- Generates 1500-word article
- SEO-optimized (meta, headings, internal links)
- One-click publish to WordPress/Medium

**Stretch goals:**
- Brand voice training (RAG over your existing content)
- Multi-language
- Content calendar
- Auto-publish to social

---

## 8-Week Build Schedule

### Week 1: Idea + Research
- [ ] Pick idea (use IDEAL framework)
- [ ] Interview 5 potential users (15 min each)
- [ ] Validate willingness to pay
- [ ] Set up GitHub repo
- [ ] Write 1-page PRD (problem, solution, success metrics)

**Deliverable:** PRD + landing page draft

### Week 2: Design + Tech Choices
- [ ] Sketch user flow (Figma, paper, or text)
- [ ] Choose tech stack (use templates above)
- [ ] Set up accounts (OpenAI, Pinecone, Stripe, etc.)
- [ ] Estimate costs ($X/month at 100 users)
- [ ] Design database schema

**Deliverable:** Architecture diagram + tech stack doc

### Week 3: Build core feature
- [ ] Implement the main LLM/RAG/agent logic
- [ ] Add basic UI (Streamlit is fine for MVP)
- [ ] Get it working end-to-end
- [ ] Test with 3 friends
- [ ] Fix the 3 worst bugs

**Deliverable:** Working MVP (even if ugly)

### Week 4: Build supporting features
- [ ] Authentication
- [ ] Payment integration (Stripe)
- [ ] Database setup
- [ ] Basic admin dashboard
- [ ] Error handling

**Deliverable:** Deployed MVP (still ugly but works)

### Week 5: Launch to first 10 users
- [ ] Polish landing page (use one of the prototypes)
- [ ] Write launch post (Twitter, LinkedIn, Reddit, relevant communities)
- [ ] Offer free access to first 10 users
- [ ] Get feedback
- [ ] Fix the 3 most-mentioned issues

**Deliverable:** 10 active users

### Week 6: Iterate based on feedback
- [ ] Add the 1 feature most-requested feature
- [ ] Improve the most-confusing UX
- [ ] Optimize the slowest part
- [ ] Add analytics (PostHog, Plausible)
- [ ] Set up error tracking (Sentry)

**Deliverable:** Improved product, 20-30 users

### Week 7: Polish + Document
- [ ] Improve UI (you're not done until you're proud to show it)
- [ ] Write README.md (what, why, how, screenshots)
- [ ] Record 2-minute demo video
- [ ] Write blog post: "How I built [product] with AI"
- [ ] Set up customer support (email, Discord, or Intercom)

**Deliverable:** Portfolio-ready product

### Week 8: Demo Day + Iterate
- [ ] Present at cohort Demo Day
- [ ] Get instructor feedback
- [ ] Plan next 90 days (monetize, grow, or kill it)
- [ ] Update LinkedIn, resume, portfolio site
- [ ] Apply to jobs (if that's the goal)

**Deliverable:** Public launch, next 90-day plan

---

## Cost estimation (for 100 users)

| Component | Monthly Cost |
|-----------|--------------|
| LLM API (GPT-4o-mini) | $30-100 |
| Embeddings (OpenAI) | $10-30 |
| Vector DB (Pinecone free → $70) | $0-70 |
| Hosting (Railway/Render) | $20-50 |
| Database (Postgres) | $15-25 |
| Storage (S3) | $5-10 |
| Domain | $1 |
| Email (Resend) | $0-20 |
| **Total** | **$80-300/mo** |

At $29/mo per user × 100 users = $2,900/mo. Margin: ~90%.

---

## Marketing your capstone (get to 100 users)

### Week 1-3: Soft launch
- 10 friends + family
- 20 people from your existing network
- 10 from relevant subreddits or Slack groups

### Week 4-6: Public launch
- Product Hunt launch (aim for top 5 of the day)
- Show HN (if B2B/dev audience)
- Twitter thread with demo video
- LinkedIn post with results

### Week 7-8: Growth
- SEO (1 blog post per week, target long-tail keywords)
- Partnerships (integrate with complementary tools)
- Paid ads (only after organic traction)

### Channels that work for AI products:
- **Twitter/X** — Build in public, share progress
- **Reddit** — r/SaaS, r/entrepreneur, niche subs
- **Hacker News** — Show HN if dev tool
- **LinkedIn** — If B2B
- **Indie Hackers** — For solo founders
- **Product Hunt** — For consumer products

---

## Common capstone mistakes

### ❌ Mistake 1: Building for 6 months without launching
**Fix:** Launch in week 5, even if it's ugly. Real users > perfect code.

### ❌ Mistake 2: Trying to build "the next ChatGPT"
**Fix:** Solve ONE problem for ONE audience. Niche > broad.

### ❌ Mistake 3: Ignoring unit economics
**Fix:** If it costs $5 to serve a $10/mo user, you have a problem. Calculate LTV/CAC before building.

### ❌ Mistake 4: No distribution strategy
**Fix:** "Build it and they will come" doesn't work. Pick a channel (Twitter, SEO, sales) before you build.

### ❌ Mistake 5: Skipping customer interviews
**Fix:** Talk to 10 potential users BEFORE writing code. Validate the problem.

### ❌ Mistake 6: Perfectionism
**Fix:** Ship at 80%. The remaining 20% takes 80% of the time.

### ❌ Mistake 7: Building alone, in silence
**Fix:** Build in public. Post updates weekly. Get feedback early.

---

## Capstone grading rubric (Cohort students)

| Criteria | Points | What we're looking for |
|----------|--------|----------------------|
| **Working product** | 25 | Deployed, accessible, core feature works |
| **Real users** | 20 | 10+ active users, evidence of usage |
| **Code quality** | 15 | Clean, documented, GitHub public |
| **Documentation** | 15 | README, blog post, demo video |
| **Technical depth** | 15 | Uses 3+ course techniques, novel combinations |
| **Demo quality** | 10 | Clear, compelling 2-minute demo |
| **Total** | 100 | |

**Grading scale:**
- 90-100: A — Featured in course showcase, instructor referrals
- 80-89: B — Strong portfolio piece, job-ready
- 70-79: C — Solid foundation, needs polish
- Below 70: Incomplete — must resubmit

---

## Capstone success stories (from past cohorts)

> **"I built an AI tool for Etsy sellers. 6 months later, I sold it for $45K."**
> — Anonymous, 2025 cohort

> **"My capstone got me a job at Anthropic. I showed it in the interview and they hired me on the spot."**
> — Jamie L., 2025 cohort

> **"I turned my capstone into a $3K/mo SaaS. The course paid for itself 60x."**
> — Raj P., 2024 cohort

> **"My capstone is now my entire consulting business. $20K/mo."**
> — Maria S., 2024 cohort

---

## Need inspiration? Browse these:

- **AI tools directories:** [There's An AI For That](https://theresanaiforthat.com), [Product Hunt AI](https://producthunt.com/topics/artificial-intelligence)
- **Indie Hackers:** Search "AI" for real revenue numbers
- **GitHub:** Look at projects with 1K+ stars in the AI space
- **Twitter:** Follow indie hackers building AI products

---

## Ready to start?

1. **Join the next cohort** (link in course platform)
2. **Or do it self-paced** with the templates above
3. **Post your idea in #capstone-ideas** for feedback
4. **Find an accountability partner** in your cohort

Your capstone is the most important part of this course. Everything else is preparation. The capstone is the proof.

Ship it. 🚀
