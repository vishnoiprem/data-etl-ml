# 08 — Sourcing Jobs

> **Lesson 8 of 9** · ~15 min

Where to find data engineering roles, how to cold-outreach to
hiring managers, and the tracking spreadsheet that keeps your
pipeline from going dark.

---

## 1. The job board landscape

There are roughly 8 boards that matter for senior+ data
engineering roles, in rough order of yield:

| Board | Yield for senior+ DE | Best for |
|---|---|---|
| **LinkedIn** | High | Volume + the only place to find recruiters by name |
| **Levels.fyi** | Medium-High | Discovery of companies paying senior+ comp, link to apply |
| **HN Who's Hiring** (monthly) | Medium | Curated, less noise, good for early-stage / non-FAANG |
| **Company career pages** (direct) | High | Bypasses aggregators, fastest ATS pass |
| **Wellfound (AngelList)** | Medium | Early-stage, equity-heavy startups |
| **DataJobs.com / DataEngJobs** | Low-Medium | Niche DE-specific boards |
| **Glassdoor / Indeed** | Low | Volume, mostly junior or non-FAANG |
| **Y Combinator's Work at a Startup** | Medium | Early-stage, equity |

**The mistake most candidates make:** defaulting to LinkedIn
Easy Apply and sending 200 applications through it. The
problems with that approach:

- **Easy Apply routes through a low-quality ATS** that many
  hiring managers distrust.
- **You have no control over how the application is presented.**
- **You have no referral path** through Easy Apply.
- **The volume is too high for you to do any targeting.**

The right approach: **use LinkedIn for discovery, but apply
through the company's career page when possible**. Use the
other boards for *supplemental* discovery, not primary volume.

---

## 2. Cold outbound to hiring managers

For senior+ roles, **cold outbound is 5-10x more effective than
applying**. The reason is that you're reaching the person who
actually decides, bypassing the entire ATS + recruiter chain.
A 5-minute cold DM from a strong candidate often gets a faster
response than a 2-week-old application.

**How to find the hiring manager:**

| Method | How it works | Yield |
|---|---|---|
| **LinkedIn search for the title at the company** | "Data Platform Manager" at [Company] | High |
| **The job post itself** | Most job posts name the hiring manager, or the team | High |
| **The team's manager, found via the company org page** | Look at the data org in LinkedIn Sales Navigator | Medium |
| **The recruiter listed on the job post** | Sometimes a "recruiter: [Name]" line | Medium |
| **Ask a friend who works there** | "Who's the data platform manager?" | High |

Once you have the name:

- **Check if they post publicly.** Many senior+ leaders post
  on LinkedIn about their team's work. Read 2-3 recent posts.
  This is the source material for the cold DM.
- **Check if they have a public GitHub or blog.** Same logic —
  their writing tells you what they care about.
- **Look for a 1st-degree connection.** If you have one, ask
  for an introduction. If not, send a connection request +
  DM.

---

## 3. The cold DM template

A cold DM to a hiring manager has 4 parts, in this order:

1. **Who you are** (1 sentence, with the title-and-stack signal)
2. **Why them, specifically** (1 sentence, with a real reference
   to their work)
3. **Your 1-2 most relevant accomplishments** (2 sentences, XYZ
   format)
4. **The ask** (1 sentence, direct)

Total: ~5 sentences, 100-150 words. Same structure as the cover
letter, but tighter.

**Sample cold DM (LinkedIn or email):**

> *Hi [Name] — I'm a senior data engineer with 5 years on
> Python + Kafka + AWS, currently leading the data platform
> work at MidPay. I saw your team's post on the streaming
> migration last month — the choice to standardize on Kafka
> Streams is the same path we took at MidPay.*
>
> *I'm exploring my next role and your team's charter is the
> closest match I've found to the work I want to do. My most
> relevant work: led a 14 TB Hadoop → AWS migration, zero
> downtime, $280k/yr savings; built a Kafka pipeline ingesting
> 800M events/day with 99.9% delivery SLA.*
>
> *Would you be open to a 15-min chat about the role? I'm
> flexible on timing. Thanks for reading.*

What makes this work:

- **Specific reference** to the hiring manager's own work
  (signals you did 5 minutes of research)
- **Same-stack signal** in paragraph 1 (the manager can place
  you in 3 seconds)
- **2 bullets, in XYZ format** (the manager can decide if the
  scope is right in 10 seconds)
- **A specific ask** (15 min, not "an exploratory conversation")
- **No "I'm a huge fan of [Company]"** (the manager doesn't
  care)

**Response rate:** cold DMs to senior+ hiring managers in DE
have a 15-25% response rate when they reference a specific piece
of the manager's work. The rate drops to 3-5% when the DM is
generic. The 5 minutes of research is the highest-leverage
work in your job search.

---

## 4. The "warm intro > cold apply" rule

The data is unambiguous: **a warm intro (referral, internal
mobility, cold DM that turns into a conversation) converts at
2-5x the rate of a cold apply**. The mechanism is that warm
intros *bypass* the ATS, which is the gate that filters out 75%
of applications.

The numbers for senior+ data engineering roles:

| Application path | Response rate | Time to screen |
|---|---|---|
| **Cold apply via LinkedIn Easy Apply** | 1-3% | 3-6 weeks |
| **Cold apply via company career page** | 3-7% | 2-4 weeks |
| **Targeted apply with cover letter (no referral)** | 5-10% | 1-3 weeks |
| **Cold DM to hiring manager** | 15-25% | 1-2 weeks |
| **Apply with a referral from a peer** | 30-50% | 3-7 days |
| **Apply with a referral from a senior+ employee** | 50-70% | 1-3 days |
| **Internal transfer (with manager support)** | 60-80% | 1-2 weeks |

The compounding is real. A single senior+ referral can replace
20 cold applies. **Spend 1 hour finding a senior+ referrer; you
will save 20 hours of cold-applying.**

The mechanics of getting a referral is Lesson 09. For now,
internalize the rule: **the warm intro is the single highest-
leverage move in your job search**.

---

## 5. The tracking spreadsheet

The single biggest reason candidates lose track of their job
search is they have no system. They send 30 applications, get
5 responses, lose track of which is which, follow up with the
wrong person, miss a deadline, and end up with 3 offers instead
of 5.

**The fix is a tracking spreadsheet.** Here's the template:

```
| Company | Role | URL | Date Applied | Source | Referrer | Status | Last Action | Next Action | Next Action Date | Notes |
```

The columns:

- **Company** — name
- **Role** — exact title from the JD
- **URL** — link to the JD
- **Date Applied** — when you submitted
- **Source** — LinkedIn, career page, referral, cold DM
- **Referrer** — name of the person who referred you (or blank)
- **Status** — Applied / Screen Scheduled / Onsite / Offer / Rejected / Withdrawn
- **Last Action** — what you did last (e.g. "sent thank-you note after screen")
- **Next Action** — what you need to do next (e.g. "follow up if no response by [date]")
- **Next Action Date** — when to do it
- **Notes** — anything else (interviewer names, salary discussed, comp expectations)

**The discipline:** every application goes in. Every action
updates the row. Every follow-up is scheduled with a date. No
exceptions. The 30 minutes of setup buys you 30 hours of
sanity over the next 3 months.

**A "status" rule of thumb:**

- If you've had no response in 7 days, send a follow-up (cold
  DM to the recruiter, or a reply to the original email).
- If you've had no response in 14 days, send a 2nd follow-up.
- If you've had no response in 21 days, mark it "Withdrawn" and
  move on.

Most candidates never follow up. The ones who do get 2-3x the
response rate, because the recruiter's queue is long and a
polite follow-up bumps you to the top.

---

## 6. The application cadence

The right cadence for a senior+ job search is **5-10 high-quality
applications per week**, not 20-30 low-quality ones.

The breakdown:

- **2-3 targeted applications** with referrals or cold DMs
  (highest yield)
- **2-3 targeted applications** via company career pages with
  cover letters
- **1-2 supplemental applications** via LinkedIn / boards (volume
  tail)

The cadence is sustainable for 4-8 weeks. After 8 weeks of
active searching with this cadence, most senior+ candidates
have 1-3 offers in hand. The ones who don't usually need to
fix the resume / cover letter / cold DM, not increase the volume.

**The anti-pattern:** sending 20 applications in week 1, getting
3 responses, and then slowing down to 1-2 per week. The pipeline
needs to be *constant* to produce a steady stream of screens.
A bursty pipeline produces a bursty stream of responses, and
most candidates can't ride the wave.

---

## 7. A worked example: 1 week in a senior+ DE job search

**Monday:**
- Find 5 new roles on LinkedIn + Levels.fyi. Add to spreadsheet.
- Send 2 cold DMs to hiring managers (15 min each).
- Apply to 2 roles via company career pages with targeted resumes
  + cover letters (45 min each).

**Tuesday:**
- Follow up on 3 applications from last week (5 min each).
- Send 1 cold DM to a senior+ employee at a target company for
  a referral (10 min).
- Apply to 1 role with a referral.

**Wednesday:**
- Take a screen call.
- Send 2 more cold DMs.
- Apply to 1 more role.

**Thursday-Sunday:** same pattern, ~1 hour per day.

**End of week:** 8-10 new applications in flight, 3-5 follow-ups
sent, 2-3 cold DMs sent, 1-2 screen calls. The pipeline is
fed, the response rate is high, and the spreadsheet has 15-20
open applications. This is a sustainable cadence.

---

## Try it

Set up your tracking spreadsheet this week. Use the template
above. Add every application to it as you send it. After your
first week, you should have:

- [ ] 5+ applications in the spreadsheet
- [ ] At least 1 cold DM to a hiring manager sent
- [ ] At least 1 follow-up on a 7+ day old application
- [ ] A "next action" with a date for every open row

The discipline of the spreadsheet is what separates a senior+
job search that lands offers from one that doesn't.
